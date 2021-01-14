import asyncio
import fnmatch
import json
import logging
import os
import threading
import webbrowser
from functools import partial
from urllib.parse import urlparse

import tornado
import tornado.httpserver
import tornado.ioloop
from tornado.web import StaticFileHandler
from tornado.websocket import WebSocketHandler

from ..session import CoroutineBasedSession, ThreadBasedSession, ScriptModeSession, \
    register_session_implement_for_target, Session
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, wait_host_port, STATIC_PATH, iscoroutinefunction, isgeneratorfunction
from .utils import make_applications

logger = logging.getLogger(__name__)

_ioloop = None


def ioloop() -> tornado.ioloop.IOLoop:
    """获得运行Tornado server的IOLoop"""
    global _ioloop
    return _ioloop


def _check_origin(origin, allowed_origins, handler: WebSocketHandler):
    if _is_same_site(origin, handler):
        return True

    return any(
        fnmatch.fnmatch(origin, patten)
        for patten in allowed_origins
    )


def _is_same_site(origin, handler: WebSocketHandler):
    parsed_origin = urlparse(origin)
    origin = parsed_origin.netloc
    origin = origin.lower()

    host = handler.request.headers.get("Host")

    # Check to see that origin matches host directly, including ports
    return origin == host


def _webio_handler(applications, check_origin_func=_is_same_site):
    """获取用于Tornado进行整合的RequestHandle类

    :param dict applications: 任务名->任务函数 的字典
    :param callable check_origin_func: check_origin_func(origin, handler) -> bool
    :return: Tornado RequestHandle类
    """

    class WSHandler(WebSocketHandler):

        def check_origin(self, origin):
            return check_origin_func(origin=origin, handler=self)

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        def send_msg_to_client(self, session: Session):
            for msg in session.get_task_commands():
                self.write_message(json.dumps(msg))

        def open(self):
            logger.debug("WebSocket opened")
            # self.set_nodelay(True)

            self._close_from_session_tag = False  # 由session主动关闭连接

            session_info = get_session_info_from_headers(self.request.headers)
            session_info['user_ip'] = self.request.remote_ip
            session_info['request'] = self.request
            session_info['backend'] = 'tornado'

            app_name = self.get_query_argument('app', 'index')
            application = applications.get(app_name) or applications['index']
            if iscoroutinefunction(application) or isgeneratorfunction(application):
                self.session = CoroutineBasedSession(application, session_info=session_info,
                                                     on_task_command=self.send_msg_to_client,
                                                     on_session_close=self.close_from_session)
            else:
                self.session = ThreadBasedSession(application, session_info=session_info,
                                                  on_task_command=self.send_msg_to_client,
                                                  on_session_close=self.close_from_session,
                                                  loop=asyncio.get_event_loop())

        def on_message(self, message):
            data = json.loads(message)
            if data is not None:
                self.session.send_client_event(data)

        def close_from_session(self):
            self._close_from_session_tag = True
            self.close()

        def on_close(self):
            if not self._close_from_session_tag:  # 只有在由客户端主动断开连接时，才调用 session.close()
                self.session.close()
            logger.debug("WebSocket closed")

    return WSHandler


def webio_handler(applications, allowed_origins=None, check_origin=None):
    """获取在Tornado中运行PyWebIO应用的RequestHandle类。RequestHandle类基于WebSocket协议与浏览器进行通讯。

    :param callable/list/dict applications: PyWebIO应用。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
    :param callable check_origin: 请求来源检查函数。

    关于各参数的详细说明见 :func:`pywebio.platform.tornado.start_server` 的同名参数。

    :return: Tornado RequestHandle类
    """
    applications = make_applications(applications)
    for target in applications.values():
        register_session_implement_for_target(target)

    if check_origin is None:
        check_origin_func = partial(_check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, handler: _is_same_site(origin, handler) or check_origin(origin)

    return _webio_handler(applications=applications, check_origin_func=check_origin_func)


async def open_webbrowser_on_server_started(host, port):
    url = 'http://%s:%s' % (host, port)
    is_open = await wait_host_port(host, port, duration=5, delay=0.5)
    if is_open:
        logger.info('Try open %s in web browser' % url)
        webbrowser.open(url)
    else:
        logger.error('Open %s failed.' % url)


def _setup_server(webio_handler, port=0, host='', **tornado_app_settings):
    if port == 0:
        port = get_free_port()

    handlers = [(r"/io", webio_handler),
                (r"/(.*)", StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'})]

    app = tornado.web.Application(handlers=handlers, **tornado_app_settings)
    server = app.listen(port, address=host)
    return server, port


def start_server(applications, port=0, host='', debug=False,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 websocket_max_message_size=None,
                 websocket_ping_interval=None,
                 websocket_ping_timeout=None,
                 **tornado_app_settings):
    """启动一个 Tornado server 将PyWebIO应用作为Web服务提供。

    Tornado为PyWebIO应用的默认后端Server，可以直接使用 ``from pywebio import start_server`` 导入。

    :param list/dict/callable applications: PyWebIO应用. 可以是任务函数或者任务函数的字典或列表。

       类型为字典时，字典键为任务名，类型为列表时，函数名为任务名。

       可以通过 ``app`` URL参数选择要运行的任务(例如访问 ``http://host:port/?app=foo`` 来运行 ``foo`` 任务)，
       默认使用运行 ``index`` 任务函数，当 ``index`` 任务不存在时，PyWebIO会提供一个默认的索引页作为主页。

       任务函数为协程函数时，使用 :ref:`基于协程的会话实现 <coroutine_based_session>` ；任务函数为普通函数时，使用基于线程的会话实现。
    :param int port: 服务监听的端口。设置为 ``0`` 时，表示自动选择可用端口。
    :param str host: 服务绑定的地址。 ``host`` 可以是IP地址或者为hostname。如果为hostname，服务会监听所有与该hostname关联的IP地址。
       通过设置 ``host`` 为空字符串或 ``None`` 来将服务绑定到所有可用的地址上。
    :param bool debug: Tornado Server是否开启debug模式
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议、域名和端口部分，允许使用 Unix shell 风格的匹配模式(全部规则参见 `Python文档 <https://docs.python.org/zh-tw/3/library/fnmatch.html>`_ ):

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq中的任何字符
        - ``[!seq]`` 匹配任何不在seq中的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com``
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议、域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :param bool auto_open_webbrowser: 当服务启动后，是否自动打开浏览器来访问服务。（该操作需要操作系统支持）
    :param int websocket_max_message_size: Tornado Server最大可接受的WebSockets消息大小。单位为字节，默认为10MiB。
    :param int websocket_ping_interval: 当被设置后，服务器会以 ``websocket_ping_interval`` 秒周期性地向每个WebSockets连接发送‘ping‘消息。
        如果应用处在某些反向代理服务器之后，设置 ``websocket_ping_interval`` 可以避免WebSockets连接被代理服务器当作空闲连接而关闭。
        同时，若WebSockets连接在某些情况下被异常关闭，应用也可以及时感知。
    :param int websocket_ping_timeout: 如果设置了 ``websocket_ping_interval`` ，而服务没有在发送‘ping‘消息后的 ``websocket_ping_timeout`` 秒
        内收到‘pong’消息，应用会将连接关闭。默认的超时时间为 ``websocket_ping_interval`` 的三倍。
    :param tornado_app_settings: 传递给 ``tornado.web.Application`` 构造函数的额外的关键字参数
        可设置项参考: https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings
    """
    kwargs = locals()
    global _ioloop
    _ioloop = tornado.ioloop.IOLoop.current()

    app_options = ['debug', 'websocket_max_message_size', 'websocket_ping_interval', 'websocket_ping_timeout']
    for opt in app_options:
        if kwargs[opt] is not None:
            tornado_app_settings[opt] = kwargs[opt]

    handler = webio_handler(applications, allowed_origins=allowed_origins, check_origin=check_origin)
    _, port = _setup_server(webio_handler=handler, port=port, host=host, **tornado_app_settings)

    print('Listen on %s:%s' % (host or '0.0.0.0', port))

    if auto_open_webbrowser:
        tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, host or 'localhost', port)
    tornado.ioloop.IOLoop.current().start()


def start_server_in_current_thread_session():
    """启动 script mode 的server，监听可用端口，并自动打开浏览器

    PYWEBIO_SCRIPT_MODE_PORT环境变量可以设置监听端口，并关闭自动打开浏览器，用于测试
    """
    websocket_conn_opened = threading.Event()
    thread = threading.current_thread()

    class SingleSessionWSHandler(_webio_handler(applications={})):
        session = None
        instance = None

        def open(self):
            self.main_session = False
            if SingleSessionWSHandler.session is None:
                self.main_session = True
                SingleSessionWSHandler.instance = self
                session_info = get_session_info_from_headers(self.request.headers)
                session_info['user_ip'] = self.request.remote_ip
                session_info['request'] = self.request
                session_info['backend'] = 'tornado'
                SingleSessionWSHandler.session = ScriptModeSession(thread, session_info=session_info,
                                                                   on_task_command=self.send_msg_to_client,
                                                                   loop=asyncio.get_event_loop())
                websocket_conn_opened.set()
            else:
                self.close()

        def on_close(self):
            if SingleSessionWSHandler.session is not None and self.main_session:
                self.session.close()
                logger.debug('ScriptModeSession closed')

    async def wait_to_stop_loop(server):
        """当只剩当前线程和Daemon线程运行时，关闭Server"""
        alive_none_daemonic_thread_cnt = None  # 包括当前线程在内的非Daemon线程数
        while alive_none_daemonic_thread_cnt != 1:
            alive_none_daemonic_thread_cnt = sum(
                1 for t in threading.enumerate() if t.is_alive() and not t.isDaemon()
            )
            await asyncio.sleep(1)

        # 关闭Websocket连接
        if SingleSessionWSHandler.instance:
            SingleSessionWSHandler.instance.close()

        server.stop()
        logger.debug('Closing tornado ioloop...')
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
        for task in tasks: task.cancel()

        # 必须需要 await asyncio.sleep ，否则 t.cancel() 调用无法调度生效
        await asyncio.sleep(0)

        tornado.ioloop.IOLoop.current().stop()

    def server_thread():
        from tornado.log import access_log, app_log, gen_log
        access_log.setLevel(logging.ERROR)
        app_log.setLevel(logging.ERROR)
        gen_log.setLevel(logging.ERROR)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        global _ioloop
        _ioloop = tornado.ioloop.IOLoop.current()

        port = 0
        if os.environ.get("PYWEBIO_SCRIPT_MODE_PORT"):
            port = int(os.environ.get("PYWEBIO_SCRIPT_MODE_PORT"))

        server, port = _setup_server(webio_handler=SingleSessionWSHandler, port=port, host='localhost')
        tornado.ioloop.IOLoop.current().spawn_callback(partial(wait_to_stop_loop, server=server))

        if "PYWEBIO_SCRIPT_MODE_PORT" not in os.environ:
            tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, 'localhost', port)

        tornado.ioloop.IOLoop.current().start()
        logger.debug('Tornado server exit')

    t = threading.Thread(target=server_thread, name='Tornado-server')
    t.start()

    websocket_conn_opened.wait()
