"""
Flask backend

.. note::
    在 CoroutineBasedSession 会话中，若在协程任务函数内调用 asyncio 中的协程函数，需要使用 asyncio_coroutine
"""
import json
import logging
import threading

from flask import Flask, request, send_from_directory, Response

from .httpbased import HttpContext, HttpHandler, run_event_loop
from ..session import register_session_implement_for_target
from ..utils import STATIC_PATH, iscoroutinefunction, isgeneratorfunction

logger = logging.getLogger(__name__)


class FlaskHttpContext(HttpContext):
    backend_name = 'flask'

    def __init__(self):
        self.response = Response()
        self.request_data = request.get_data()

    def request_obj(self):
        """返回当前请求对象"""
        return request._get_current_object()

    def request_method(self):
        """返回当前请求的方法，大写"""
        return request.method

    def request_headers(self):
        """返回当前请求的header字典"""
        return request.headers

    def request_url_parameter(self, name, default=None):
        """返回当前请求的URL参数"""
        return request.args.get(name, default=default)

    def request_json(self):
        """返回当前请求的json反序列化后的内容，若请求数据不为json格式，返回None"""
        try:
            return json.loads(self.request_data)
        except Exception:
            return None

    def set_header(self, name, value):
        """为当前响应设置header"""
        self.response.headers[name] = value

    def set_status(self, status: int):
        """为当前响应设置http status"""
        self.response.status_code = status

    def set_content(self, content, json_type=False):
        """设置相应的内容

        :param content:
        :param bool json_type: content是否要序列化成json格式，并将 content-type 设置为application/json
        """
        if json_type:
            self.set_header('content-type', 'application/json')
            self.response.data = json.dumps(content)
        else:
            self.response.data = content

    def get_response(self):
        """获取当前的响应对象，用于在私图函数中返回"""
        return self.response

    def get_client_ip(self):
        """获取用户的ip"""
        return request.remote_addr


def webio_view(target,
               session_expire_seconds=None,
               session_cleanup_interval=None,
               allowed_origins=None, check_origin=None):
    """获取在Flask中运行PyWebIO任务的视图函数。基于http请求与前端进行通讯

    :param target: 任务函数。任务函数为协程函数时，使用 :ref:`基于协程的会话实现 <coroutine_based_session>` ；任务函数为普通函数时，使用基于线程的会话实现。
    :param int session_expire_seconds: 会话不活跃过期时间。
    :param int session_cleanup_interval: 会话清理间隔。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议和域名和端口部分，允许使用 Unix shell 风格的匹配模式:

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq内的字符
        - ``[!seq]`` 匹配不在seq内的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com``
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议和域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :return: Flask视图函数
    """
    session_cls = register_session_implement_for_target(target)
    handler = HttpHandler(target=target, session_cls=session_cls,
                          session_expire_seconds=session_expire_seconds,
                          session_cleanup_interval=session_cleanup_interval,
                          allowed_origins=allowed_origins, check_origin=check_origin)

    def view_func():
        context = FlaskHttpContext()
        return handler.handle_request(context)

    view_func.__name__ = 'webio_view'
    return view_func


def start_server(target, port=8080, host='localhost',
                 allowed_origins=None, check_origin=None,
                 disable_asyncio=False,
                 session_cleanup_interval=None,
                 session_expire_seconds=None,
                 debug=False, **flask_options):
    """启动一个 Flask server 将 ``target`` 任务函数作为Web服务提供。

    :param target: 任务函数。任务函数为协程函数时，使用 :ref:`基于协程的会话实现 <coroutine_based_session>` ；任务函数为普通函数时，使用基于线程的会话实现。
    :param int port: server bind port. set ``0`` to find a free port number to use
    :param str host: server bind host. ``host`` may be either an IP address or hostname.  If it's a hostname,
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议和域名和端口部分，允许使用 Unix shell 风格的匹配模式:

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq内的字符
        - ``[!seq]`` 匹配不在seq内的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com``
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议和域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :param bool disable_asyncio: 禁用 asyncio 函数。仅在 ``target`` 为协程函数时有效。

       .. note::  实现说明：
           当使用Flask backend时，若要在PyWebIO的会话中使用 ``asyncio`` 标准库里的协程函数，PyWebIO需要单独开启一个线程来运行 ``asyncio`` 事件循环，
           若程序中没有使用到 ``asyncio`` 中的异步函数，可以开启此选项来避免不必要的资源浪费

    :param int session_expire_seconds: 会话过期时间。若 session_expire_seconds 秒内没有收到客户端的请求，则认为会话过期。
    :param int session_cleanup_interval: 会话清理间隔。
    :param bool debug: Flask debug mode
    :param flask_options: Additional keyword arguments passed to the constructor of ``flask.Flask.run``.
        ref: https://flask.palletsprojects.com/en/1.1.x/api/?highlight=flask%20run#flask.Flask.run
    """

    app = Flask(__name__)
    app.add_url_rule('/io', 'webio_view', webio_view(
        target,
        session_expire_seconds=session_expire_seconds,
        session_cleanup_interval=session_cleanup_interval,
        allowed_origins=allowed_origins,
        check_origin=check_origin
    ), methods=['GET', 'POST', 'OPTIONS'])

    @app.route('/')
    @app.route('/<path:static_file>')
    def serve_static_file(static_file='index.html'):
        return send_from_directory(STATIC_PATH, static_file)

    if not disable_asyncio and (iscoroutinefunction(target) or isgeneratorfunction(target)):
        threading.Thread(target=run_event_loop, daemon=True).start()

    if not debug:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    app.run(host=host, port=port, debug=debug, **flask_options)
