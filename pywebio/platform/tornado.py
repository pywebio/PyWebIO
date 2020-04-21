import asyncio
import fnmatch
import json
import logging
import threading
import webbrowser
from functools import partial
from urllib.parse import urlparse
import os

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.websocket
from tornado.web import StaticFileHandler
from tornado.websocket import WebSocketHandler
from ..session import CoroutineBasedSession, ThreadBasedSession, ScriptModeSession, \
    register_session_implement_for_target, AbstractSession
from ..utils import get_free_port, wait_host_port, STATIC_PATH

logger = logging.getLogger(__name__)


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


def _webio_handler(target, session_cls, check_origin_func=_is_same_site):
    """获取用于Tornado进行整合的RequestHandle类

    :param target: 任务函数
    :param session_cls: 会话实现类
    :param callable check_origin_func: check_origin_func(origin, handler) -> bool
    :return: Tornado RequestHandle类
    """

    class WSHandler(WebSocketHandler):

        def check_origin(self, origin):
            return check_origin_func(origin=origin, handler=self)

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        def send_msg_to_client(self, session: AbstractSession):
            for msg in session.get_task_commands():
                self.write_message(json.dumps(msg))

        def open(self):
            logger.debug("WebSocket opened")
            self.set_nodelay(True)

            self._close_from_session_tag = False  # 由session主动关闭连接

            if session_cls is CoroutineBasedSession:
                self.session = CoroutineBasedSession(target, on_task_command=self.send_msg_to_client,
                                                     on_session_close=self.close_from_session)
            elif session_cls is ThreadBasedSession:
                self.session = ThreadBasedSession(target, on_task_command=self.send_msg_to_client,
                                                  on_session_close=self.close_from_session,
                                                  loop=asyncio.get_event_loop())
            else:
                raise RuntimeError("Don't support session type:%s" % session_cls)

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


def webio_handler(target, allowed_origins=None, check_origin=None):
    """获取用于Tornado进行整合的RequestHandle类

    :param target: 任务函数。任务函数为协程函数时，使用 :ref:`基于协程的会话实现 <coroutine_based_session>` ；任务函数为普通函数时，使用基于线程的会话实现。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议和域名和端口部分，允许使用 Unix shell 风格的匹配模式:

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq内的字符
        - ``[!seq]`` 匹配不在seq内的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com`` 、
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议和域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :return: Tornado RequestHandle类
    """
    session_cls = register_session_implement_for_target(target)

    if check_origin is None:
        check_origin_func = _is_same_site
        if allowed_origins:
            check_origin_func = partial(_check_origin, allowed_origins=allowed_origins)
    else:
        check_origin_func = lambda origin, handler: _is_same_site(origin, handler) or check_origin(origin)

    return _webio_handler(target=target, session_cls=session_cls, check_origin_func=check_origin_func)


async def open_webbrowser_on_server_started(host, port):
    url = 'http://%s:%s' % (host, port)
    is_open = await wait_host_port(host, port, duration=5, delay=0.5)
    if is_open:
        logger.info('Openning %s' % url)
        webbrowser.open(url)
    else:
        logger.error('Open %s failed.' % url)


def _setup_server(webio_handler, port=0, host='', **tornado_app_settings):
    if port == 0:
        port = get_free_port()

    print('Listen on %s:%s' % (host or '0.0.0.0', port))

    handlers = [(r"/io", webio_handler),
                (r"/(.*)", StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'})]

    app = tornado.web.Application(handlers=handlers, **tornado_app_settings)
    server = app.listen(port, address=host)
    return server, port


def start_server(target, port=0, host='', debug=False,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 websocket_max_message_size=None,
                 websocket_ping_interval=None,
                 websocket_ping_timeout=None,
                 **tornado_app_settings):
    """Start a Tornado server to serve `target` function

    :param target: 任务函数。任务函数为协程函数时，使用 :ref:`基于协程的会话实现 <coroutine_based_session>` ；任务函数为普通函数时，使用基于线程的会话实现。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
    :param port: server bind port. set ``0`` to find a free port number to use
    :param host: server bind host. ``host`` may be either an IP address or hostname.  If it's a hostname,
        the server will listen on all IP addresses associated with the name.
        set empty string or to listen on all available interfaces.
    :param bool debug: Tornado debug mode
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议和域名和端口部分，允许使用 Unix shell 风格的匹配模式:

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq内的字符
        - ``[!seq]`` 匹配不在seq内的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com``
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议和域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :param bool auto_open_webbrowser: Whether or not auto open web browser when server is started (if the operating system allows it) .
    :param int websocket_max_message_size: Max bytes of a message which Tornado can accept.
        Messages larger than the ``websocket_max_message_size`` (default 10MiB) will not be accepted.
    :param int websocket_ping_interval: If set to a number, all websockets will be pinged every n seconds.
        This can help keep the connection alive through certain proxy servers which close idle connections,
        and it can detect if the websocket has failed without being properly closed.
    :param int websocket_ping_timeout: If the ping interval is set, and the server doesn’t receive a ‘pong’
        in this many seconds, it will close the websocket. The default is three times the ping interval,
        with a minimum of 30 seconds. Ignored if ``websocket_ping_interval`` is not set.
    :param tornado_app_settings: Additional keyword arguments passed to the constructor of ``tornado.web.Application``.
        ref: https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings
    """
    kwargs = locals()

    app_options = ['debug', 'websocket_max_message_size', 'websocket_ping_interval', 'websocket_ping_timeout']
    for opt in app_options:
        if kwargs[opt] is not None:
            tornado_app_settings[opt] = kwargs[opt]

    handler = webio_handler(target, allowed_origins=allowed_origins, check_origin=check_origin)
    _, port = _setup_server(webio_handler=handler, port=port, host=host, **tornado_app_settings)
    if auto_open_webbrowser:
        tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, host or 'localhost', port)
    tornado.ioloop.IOLoop.current().start()


def start_server_in_current_thread_session():
    """启动 script mode 的server，监听可用端口，并自动打开浏览器

    PYWEBIO_SCRIPT_MODE_PORT环境变量可以设置监听端口，并关闭自动打开浏览器，用于测试
    """
    websocket_conn_opened = threading.Event()
    thread = threading.current_thread()

    class SingleSessionWSHandler(_webio_handler(target=None, session_cls=None)):
        session = None

        def open(self):
            self.main_session = False
            if SingleSessionWSHandler.session is None:
                self.main_session = True
                SingleSessionWSHandler.session = ScriptModeSession(thread,
                                                                   on_task_command=self.send_msg_to_client,
                                                                   loop=asyncio.get_event_loop())
                websocket_conn_opened.set()
            else:
                self.close()

        def on_close(self):
            if SingleSessionWSHandler.session is not None and self.main_session:
                self.session.close()
                logger.debug('ScriptModeSession closed')

    async def wait_to_stop_loop():
        """当只剩当前线程和Daemon线程运行时，关闭Server"""
        alive_none_daemonic_thread_cnt = None  # 包括当前线程在内的非Daemon线程数
        while alive_none_daemonic_thread_cnt != 1:
            alive_none_daemonic_thread_cnt = sum(
                1 for t in threading.enumerate() if t.is_alive() and not t.isDaemon()
            )
            await asyncio.sleep(1)

        # 关闭ScriptModeSession。
        # 主动关闭ioloop时，SingleSessionWSHandler.on_close 并不会被调用，需要手动关闭session
        if SingleSessionWSHandler.session:
            SingleSessionWSHandler.session.close()

        # Current thread is only one none-daemonic-thread, so exit
        logger.debug('Closing tornado ioloop...')
        tornado.ioloop.IOLoop.current().stop()

    def server_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        port = 0
        if os.environ.get("PYWEBIO_SCRIPT_MODE_PORT"):
            port = int(os.environ.get("PYWEBIO_SCRIPT_MODE_PORT"))
        server, port = _setup_server(webio_handler=SingleSessionWSHandler, port=port, host='localhost')
        tornado.ioloop.IOLoop.current().spawn_callback(wait_to_stop_loop)
        if "PYWEBIO_SCRIPT_MODE_PORT" not in os.environ:
            tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, 'localhost', port)

        tornado.ioloop.IOLoop.current().start()
        logger.debug('Tornado server exit')

    t = threading.Thread(target=server_thread, name='Tornado-server')
    t.start()

    websocket_conn_opened.wait()
