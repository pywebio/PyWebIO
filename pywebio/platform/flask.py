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
from .utils import make_applications, cdn_validation
from ..utils import STATIC_PATH, iscoroutinefunction, isgeneratorfunction
from ..utils import get_free_port

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
        # self.response.data accept str and bytes
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


def webio_view(applications, cdn=True,
               session_expire_seconds=None,
               session_cleanup_interval=None,
               allowed_origins=None, check_origin=None):
    """Get the view function for running PyWebIO applications in Flask.
    The view communicates with the browser by HTTP protocol.

    :param list/dict/callable applications: PyWebIO application.
    :param bool/str cdn: 是否从CDN加载前端静态资源，默认为 ``True`` 。设置成 ``False`` 时会从PyWebIO应用部署URL的同级目录下加载静态资源。
       支持传入自定义的URL来指定静态资源的部署地址
    :param int session_expire_seconds: Session expiration time.
    :param int session_cleanup_interval: Session cleanup interval, in seconds.
    :param list allowed_origins: Allowed request source list.
    :param callable check_origin: The validation function for request source.

    The arguments of ``webio_view()`` have the same meaning as for :func:`pywebio.platform.flask.start_server`
    """

    cdn = cdn_validation(cdn, 'error')

    handler = HttpHandler(applications=applications, cdn=cdn,
                          session_expire_seconds=session_expire_seconds,
                          session_cleanup_interval=session_cleanup_interval,
                          allowed_origins=allowed_origins, check_origin=check_origin)

    def view_func():
        context = FlaskHttpContext()
        return handler.handle_request(context)

    view_func.__name__ = 'webio_view'
    return view_func


def start_server(applications, port=8080, host='localhost', cdn=True,
                 allowed_origins=None, check_origin=None,
                 session_expire_seconds=None,
                 session_cleanup_interval=None,
                 debug=False, **flask_options):
    """Start a Flask server to provide the PyWebIO application as a web service.

    :param list/dict/callable applications: PyWebIO application.
       The argument has the same meaning and format as for :func:`pywebio.platform.tornado.start_server`
    :param int port: The port the server listens on.
       When set to ``0``, the server will automatically select a available port.
    :param str host: The host the server listens on. ``host`` may be either an IP address or hostname. If it’s a hostname, the server will listen on all IP addresses associated with the name. ``host`` may be an empty string or None to listen on all available interfaces.
    :param bool/str cdn: 是否从CDN加载前端静态资源，默认为 ``True`` 。支持传入自定义的URL来指定静态资源的部署地址
    :param list allowed_origins: Allowed request source list.
       The argument has the same meaning as for :func:`pywebio.platform.tornado.start_server`
    :param callable check_origin: The validation function for request source.
       The argument has the same meaning and format as for :func:`pywebio.platform.tornado.start_server`
    :param int session_expire_seconds: Session expiration time.
       If no client message is received within ``session_expire_seconds``, the session will be considered expired.
    :param int session_cleanup_interval: Session cleanup interval, in seconds.
       The server will periodically clean up expired sessions and release the resources occupied by the sessions.
    :param bool debug: Flask debug mode.
       If enabled, the server will automatically reload for code changes.
    :param flask_options: Additional keyword arguments passed to the ``flask.Flask.run``.
       For details, please refer: https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.run
    """
    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    cdn = cdn_validation(cdn, 'warn')

    app = Flask(__name__)
    app.add_url_rule('/', 'webio_view', webio_view(
        applications=applications, cdn=cdn,
        session_expire_seconds=session_expire_seconds,
        session_cleanup_interval=session_cleanup_interval,
        allowed_origins=allowed_origins,
        check_origin=check_origin
    ), methods=['GET', 'POST', 'OPTIONS'])

    @app.route('/<path:static_file>')
    def serve_static_file(static_file):
        return send_from_directory(STATIC_PATH, static_file)

    has_coro_target = any(iscoroutinefunction(target) or isgeneratorfunction(target) for
                          target in make_applications(applications).values())
    if has_coro_target:
        threading.Thread(target=run_event_loop, daemon=True).start()

    if not debug:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    app.run(host=host, port=port, debug=debug, **flask_options)
