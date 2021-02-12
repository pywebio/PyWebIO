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

from .utils import make_applications, render_page, cdn_validation
from ..session import CoroutineBasedSession, ThreadBasedSession, ScriptModeSession, \
    register_session_implement_for_target, Session
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, wait_host_port, STATIC_PATH, iscoroutinefunction, isgeneratorfunction, check_webio_js

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


def _webio_handler(applications, cdn, check_origin_func=_is_same_site):
    """获取用于Tornado进行整合的RequestHandle类

    :param dict applications: 任务名->任务函数 的字典
    :param bool/str cdn:
    :param callable check_origin_func: check_origin_func(origin, handler) -> bool
    :return: Tornado RequestHandler类
    """
    check_webio_js()

    class WSHandler(WebSocketHandler):

        async def get(self, *args, **kwargs) -> None:
            # It's a simple http GET request
            if self.request.headers.get("Upgrade", "").lower() != "websocket":
                # Backward compatible
                if self.get_query_argument('test', ''):
                    return self.write('')

                app_name = self.get_query_argument('app', 'index')
                app = applications.get(app_name) or applications['index']
                html = render_page(app, protocol='ws', cdn=cdn)
                return self.write(html)
            else:
                await super().get()

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


def webio_handler(applications, cdn=True, allowed_origins=None, check_origin=None):
    """Get the ``RequestHandler`` class for running PyWebIO applications in Tornado.
    The ``RequestHandler`` communicates with the browser by WebSocket protocol.

    The arguments of ``webio_handler()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`
    """
    applications = make_applications(applications)
    for target in applications.values():
        register_session_implement_for_target(target)

    cdn = cdn_validation(cdn, 'error')

    if check_origin is None:
        check_origin_func = partial(_check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, handler: _is_same_site(origin, handler) or check_origin(origin)

    return _webio_handler(applications=applications, cdn=cdn, check_origin_func=check_origin_func)


async def open_webbrowser_on_server_started(host, port):
    url = 'http://%s:%s' % (host, port)
    is_open = await wait_host_port(host, port, duration=20)
    if is_open:
        logger.info('Try open %s in web browser' % url)
        webbrowser.open(url)
    else:
        logger.error('Open %s failed.' % url)


def _setup_server(webio_handler, port=0, host='', **tornado_app_settings):
    if port == 0:
        port = get_free_port()

    handlers = [(r"/", webio_handler),
                (r"/(.*)", StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'})]

    app = tornado.web.Application(handlers=handlers, **tornado_app_settings)
    server = app.listen(port, address=host)
    return server, port


def start_server(applications, port=0, host='',
                 debug=False, cdn=True,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 websocket_max_message_size=None,
                 websocket_ping_interval=None,
                 websocket_ping_timeout=None,
                 **tornado_app_settings):
    """启动一个 Tornado server 将PyWebIO应用作为Web服务提供。

    Tornado is the default backend server for PyWebIO applications,
    and ``start_server`` can be imported directly using ``from pywebio import start_server``.

    :param list/dict/callable applications: PyWebIO application.
       Can be a task function, a list of functions, or a dictionary.

       When it is a dictionary, whose key is task name and value is task function.
       When it is a list, using function name as task name.

       You can select the task to run through the ``app`` URL parameter (for example, visit ``http://host:port/?app=foo`` to run the ``foo`` task),
       By default, the ``index`` task function is used. When the ``index`` task does not exist, PyWebIO will provide a default index home page.
       See also :ref:`Server mode <server_and_script_mode>`

       When the task function is a coroutine function, use :ref:`Coroutine-based session <coroutine_based_session>` implementation,
       otherwise, use thread-based session implementation.
    :param int port: The port the server listens on.
       When set to ``0``, the server will automatically select a available port.
    :param str host: The host the server listens on. ``host`` may be either an IP address or hostname. If it’s a hostname, the server will listen on all IP addresses associated with the name. ``host`` may be an empty string or None to listen on all available interfaces.
    :param bool debug: Tornado Server's debug mode. If enabled, the server will automatically reload for code changes.
       See `tornado doc <https://www.tornadoweb.org/en/stable/guide/running.html#debug-mode>`_ for more detail.
    :param bool/str cdn: 是否从CDN加载前端静态资源，默认为 ``True`` 。支持传入自定义的URL来指定静态资源的部署地址
    :param list allowed_origins: The allowed request source list. (The current server host is always allowed)
       The source contains the protocol, domain name, and port part.
       Can use Unix shell-style wildcards:

        - ``*`` matches everything
        - ``?`` matches any single character
        - ``[seq]`` matches any character in *seq*
        - ``[!seq]`` matches any character not in *seq*

        Such as: ``https://*.example.com`` 、 ``*://*.example.com``

        For detail, see `Python Doc <https://docs.python.org/zh-tw/3/library/fnmatch.html>`_
    :param callable check_origin: The validation function for request source.
       It receives the source string (which contains protocol, host, and port parts) as parameter and return ``True/False`` to indicate that the server accepts/rejects the request.
       If ``check_origin`` is set, the ``allowed_origins`` parameter will be ignored.
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
        For details, please refer: https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings
    """
    kwargs = locals()
    global _ioloop
    _ioloop = tornado.ioloop.IOLoop.current()

    app_options = ['debug', 'websocket_max_message_size', 'websocket_ping_interval', 'websocket_ping_timeout']
    for opt in app_options:
        if kwargs[opt] is not None:
            tornado_app_settings[opt] = kwargs[opt]

    cdn = cdn_validation(cdn, 'warn')

    handler = webio_handler(applications, cdn, allowed_origins=allowed_origins, check_origin=check_origin)
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

    mock_apps = dict(index=lambda: None)

    class SingleSessionWSHandler(_webio_handler(applications=mock_apps, cdn=False)):
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
