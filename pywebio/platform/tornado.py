import asyncio
import fnmatch
import json
import logging
import os
import threading
import typing
import webbrowser
from functools import partial
from typing import Callable, Dict, List, Optional, Union
from urllib.parse import urlparse

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from . import page
from .adaptor import ws as ws_adaptor
from .page import make_applications, render_page
from .remote_access import start_remote_access_service
from .utils import cdn_validation, print_listen_address, deserialize_binary_event
from ..session import ScriptModeSession, register_session_implement_for_target, Session
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, wait_host_port, STATIC_PATH, check_webio_js, parse_file_size

logger = logging.getLogger(__name__)

_ioloop = None


def set_ioloop(loop):
    global _ioloop
    _ioloop = loop


def ioloop() -> tornado.ioloop.IOLoop:
    """获得运行Tornado server的IOLoop

    本方法当前仅在显示boken app时使用
    This method is currently only used when displaying boken app"""
    global _ioloop
    return _ioloop


def _check_origin(origin, allowed_origins, handler: tornado.websocket.WebSocketHandler):
    if _is_same_site(origin, handler):
        return True

    return any(
        fnmatch.fnmatch(origin, pattern)
        for pattern in allowed_origins
    )


def _is_same_site(origin, handler: tornado.websocket.WebSocketHandler):
    parsed_origin = urlparse(origin)
    origin = parsed_origin.netloc
    origin = origin.lower()

    host = handler.request.headers.get("Host")

    # Check to see that origin matches host directly, including ports
    return origin == host


class WebSocketConnection(ws_adaptor.WebSocketConnection):

    def __init__(self, context: tornado.websocket.WebSocketHandler):
        self.context = context

    def get_query_argument(self, name) -> typing.Optional[str]:
        return self.context.get_query_argument(name, None)

    def make_session_info(self) -> dict:
        session_info = get_session_info_from_headers(self.context.request.headers)
        session_info['user_ip'] = self.context.request.remote_ip
        session_info['request'] = self.context.request
        session_info['backend'] = 'tornado'
        session_info['protocol'] = 'websocket'
        return session_info

    def write_message(self, message: dict):
        self.context.write_message(json.dumps(message))

    def closed(self) -> bool:
        return not bool(self.context.ws_connection)

    def close(self):
        self.context.close()


def _webio_handler(applications=None, cdn=True, reconnect_timeout=0, check_origin_func=_is_same_site) \
        -> tornado.websocket.WebSocketHandler:  # noqa: C901
    """
    :param dict applications: dict of `name -> task function`
    :param bool/str cdn: Whether to load front-end static resources from CDN
    :param callable check_origin_func: check_origin_func(origin, handler) -> bool
    :return: Tornado RequestHandler class
    """
    check_webio_js()

    if applications is None:
        applications = dict(index=lambda: None)  # mock PyWebIO app

    ws_adaptor.set_expire_second(reconnect_timeout)
    tornado.ioloop.IOLoop.current().spawn_callback(ws_adaptor.session_clean_task)

    class Handler(tornado.websocket.WebSocketHandler):

        def get_app(self):
            app_name = self.get_query_argument('app', 'index')
            app = applications.get(app_name) or applications['index']
            return app

        def get_cdn(self):
            if cdn is True and self.get_query_argument('_pywebio_cdn', '') == 'false':
                return False
            return cdn

        async def get(self, *args, **kwargs) -> None:
            """http GET request"""
            if self.request.headers.get("Upgrade", "").lower() != "websocket":
                # Backward compatible
                # Frontend detect whether the backend is http server
                if self.get_query_argument('test', ''):
                    return self.write('')

                app = self.get_app()
                html = render_page(app, protocol='ws', cdn=self.get_cdn())
                return self.write(html)
            else:
                await super().get()

        def check_origin(self, origin):
            return check_origin_func(origin=origin, handler=self)

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        _handler: ws_adaptor.WebSocketHandler

        def open(self):
            conn = WebSocketConnection(self)
            self._handler = ws_adaptor.WebSocketHandler(
                connection=conn, application=self.get_app(), reconnectable=bool(reconnect_timeout)
            )

        def on_message(self, message):
            self._handler.send_client_data(message)

        def on_close(self):
            self._handler.notify_connection_lost()

    return Handler


def webio_handler(applications, cdn=True, reconnect_timeout=0, allowed_origins=None, check_origin=None):
    """Get the ``RequestHandler`` class for running PyWebIO applications in Tornado.
    The ``RequestHandler`` communicates with the browser by WebSocket protocol.

    The arguments of ``webio_handler()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`
    """
    applications = make_applications(applications)
    for target in applications.values():
        register_session_implement_for_target(target)

    cdn = cdn_validation(cdn, 'error')  # if CDN is not available, raise error

    if check_origin is None:
        check_origin_func = partial(_check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, handler: _is_same_site(origin, handler) or check_origin(origin)

    return _webio_handler(applications=applications, cdn=cdn, check_origin_func=check_origin_func,
                          reconnect_timeout=reconnect_timeout)


async def open_webbrowser_on_server_started(host, port):
    url = 'http://%s:%s' % (host, port)
    is_open = await wait_host_port(host, port, duration=20)
    if is_open:
        logger.info('Try open %s in web browser' % url)
        # webbrowser.open() may block, so invoke it in thread
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    else:
        logger.error('Open %s in web browser failed.' % url)


def _setup_server(webio_handler, port=0, host='', static_dir=None, max_buffer_size=2 ** 20 * 200,
                  **tornado_app_settings):
    if port == 0:
        port = get_free_port()

    handlers = [(r"/", webio_handler)]

    if static_dir is not None:
        handlers.append((r"/static/(.*)", tornado.web.StaticFileHandler, {"path": static_dir}))

    handlers.append((r"/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'}))

    app = tornado.web.Application(handlers=handlers, **tornado_app_settings)
    # Credit: https://stackoverflow.com/questions/19074972/content-length-too-long-when-uploading-file-using-tornado
    server = app.listen(port, address=host, max_buffer_size=max_buffer_size)
    return server, port


def start_server(applications: Union[Callable[[], None], List[Callable[[], None]], Dict[str, Callable[[], None]]],
                 port: int = 0, host: str = '', debug: bool = False, cdn: Union[bool, str] = True,
                 static_dir: Optional[str] = None, remote_access: bool = False, reconnect_timeout: int = 0,
                 allowed_origins: Optional[List[str]] = None, check_origin: Callable[[str], bool] = None,
                 auto_open_webbrowser: bool = False, max_payload_size: Union[int, str] = '200M',
                 **tornado_app_settings):
    """Start a Tornado server to provide the PyWebIO application as a web service.

    The Tornado server communicates with the browser by WebSocket protocol.

    Tornado is the default backend server for PyWebIO applications,
    and ``start_server`` can be imported directly using ``from pywebio import start_server``.

    :param list/dict/callable applications: PyWebIO application.
       Can be a task function, a list of functions, or a dictionary.
       Refer to :ref:`Advanced topic: Multiple applications in start_server() <multiple_app>` for more information.

       When the task function is a coroutine function, use :ref:`Coroutine-based session <coroutine_based_session>` implementation,
       otherwise, use thread-based session implementation.
    :param int port: The port the server listens on.
       When set to ``0``, the server will automatically select a available port.
    :param str host: The host the server listens on. ``host`` may be either an IP address or hostname.
       If it’s a hostname, the server will listen on all IP addresses associated with the name.
       ``host`` may be an empty string or None to listen on all available interfaces.
    :param bool debug: Tornado Server's debug mode. If enabled, the server will automatically reload for code changes.
       See `tornado doc <https://www.tornadoweb.org/en/stable/guide/running.html#debug-mode>`_ for more detail.
    :param bool/str cdn: Whether to load front-end static resources from CDN, the default is ``True``.
       Can also use a string to directly set the url of PyWebIO static resources.
    :param str static_dir: The directory to store the application static files.
       The files in this directory can be accessed via ``http://<host>:<port>/static/files``.
       For example, if there is a ``A/B.jpg`` file in ``static_dir`` path,
       it can be accessed via ``http://<host>:<port>/static/A/B.jpg``.
    :param bool remote_access: Whether to enable remote access, when enabled,
       you can get a temporary public network access address for the current application,
       others can access your application via this address.
    :param bool auto_open_webbrowser: Whether or not auto open web browser when server is started (if the operating system allows it) .
    :param int reconnect_timeout: The client can reconnect to server within ``reconnect_timeout`` seconds after an unexpected disconnection.
       If set to 0 (default), once the client disconnects, the server session will be closed.
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
       It receives the source string (which contains protocol, host, and port parts) as parameter and
       return ``True/False`` to indicate that the server accepts/rejects the request.
       If ``check_origin`` is set, the ``allowed_origins`` parameter will be ignored.
    :param bool auto_open_webbrowser: Whether or not auto open web browser when server is started (if the operating system allows it) .
    :param int/str max_payload_size: Max size of a websocket message which Tornado can accept.
        Messages larger than the ``max_payload_size`` (default 200MB) will not be accepted.
        ``max_payload_size`` can be a integer indicating the number of bytes, or a string ending with `K` / `M` / `G`
        (representing kilobytes, megabytes, and gigabytes, respectively).
        E.g: ``500``, ``'40K'``, ``'3M'``
    :param tornado_app_settings: Additional keyword arguments passed to the constructor of ``tornado.web.Application``.
        For details, please refer: https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings
    """
    set_ioloop(tornado.ioloop.IOLoop.current())  # to enable bokeh app

    cdn = cdn_validation(cdn, 'warn')  # if CDN is not available, warn user and disable CDN

    page.MAX_PAYLOAD_SIZE = max_payload_size = parse_file_size(max_payload_size)

    # covered `os.environ.get()` func with `bool()` to pervent type check error
    debug = Session.debug = bool(os.environ.get('PYWEBIO_DEBUG', debug))

    # Since some cloud server may close idle connections (such as heroku),
    # use `websocket_ping_interval` to  keep the connection alive
    tornado_app_settings.setdefault('websocket_ping_interval', 30)
    tornado_app_settings.setdefault('websocket_max_message_size', max_payload_size)  # Backward compatible
    tornado_app_settings['websocket_max_message_size'] = parse_file_size(
        tornado_app_settings['websocket_max_message_size'])
    tornado_app_settings['debug'] = debug
    handler = webio_handler(applications, cdn, allowed_origins=allowed_origins, check_origin=check_origin,
                            reconnect_timeout=reconnect_timeout)
    _, port = _setup_server(webio_handler=handler, port=port, host=host, static_dir=static_dir,
                            max_buffer_size=max_payload_size, **tornado_app_settings)

    print_listen_address(host, port)

    if auto_open_webbrowser:
        tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, host or '127.0.0.1', port)

    if remote_access:
        start_remote_access_service(local_port=port)

    tornado.ioloop.IOLoop.current().start()


def start_server_in_current_thread_session():
    """启动 script mode 的server，监听可用端口，并自动打开浏览器
    Start the server for script mode, and automatically open the browser when the server port is available.

    PYWEBIO_SCRIPT_MODE_PORT环境变量可以设置监听端口，并关闭自动打开浏览器，用于测试
    The PYWEBIO_SCRIPT_MODE_PORT environment variable can set the listening port, just used in testing.
    """
    websocket_conn_opened = threading.Event()
    thread = threading.current_thread()

    class SingleSessionWSHandler(_webio_handler(cdn=False)):
        session: ScriptModeSession = None
        instance: typing.ClassVar = None
        closed = False

        def send_msg_to_client(self, session):
            for msg in session.get_task_commands():
                try:
                    self.write_message(json.dumps(msg))
                except TypeError as e:
                    logger.exception('Data serialization error: %s\n'
                                     'This may be because you pass the wrong type of parameter to the function'
                                     ' of PyWebIO.\nData content: %s', e, msg)

        def open(self):
            if SingleSessionWSHandler.session is None:
                SingleSessionWSHandler.instance = self
                session_info = get_session_info_from_headers(self.request.headers)
                session_info['user_ip'] = self.request.remote_ip
                session_info['request'] = self.request
                session_info['backend'] = 'tornado'
                session_info['protocol'] = 'websocket'
                self.session = SingleSessionWSHandler.session = ScriptModeSession(
                    thread, session_info=session_info,
                    on_task_command=self.send_msg_to_client,
                    loop=asyncio.get_event_loop())
                websocket_conn_opened.set()
            else:
                self.close()

        def on_message(self, data):
            if isinstance(data, bytes):
                event = deserialize_binary_event(data)
            else:
                event = json.loads(data)
            if event is None:
                return
            self.session.send_client_event(event)

        def on_close(self):
            if self.session is not None:
                self.session.close()
                self.closed = True
                logger.debug('ScriptModeSession closed')

    async def wait_to_stop_loop(server):
        """当只剩当前线程和Daemon线程运行时，关闭Server
        When only the current thread and Daemon thread are running, close the Server"""

        # 包括当前线程在内的非Daemon线程数
        # The number of non-Daemon threads(including the current thread)
        alive_none_daemonic_thread_cnt = None
        while alive_none_daemonic_thread_cnt != 1:
            alive_none_daemonic_thread_cnt = sum(
                1 for t in threading.enumerate() if t.is_alive() and not t.isDaemon()
            )
            await asyncio.sleep(0.5)

        if SingleSessionWSHandler.session and SingleSessionWSHandler.session.need_keep_alive():
            while not SingleSessionWSHandler.instance.closed:
                await asyncio.sleep(0.5)

        # 关闭Websocket连接
        # Close the Websocket connection
        if SingleSessionWSHandler.instance:
            SingleSessionWSHandler.instance.close()

        server.stop()
        logger.debug('Closing tornado ioloop...')
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
        for task in tasks:
            task.cancel()

        # 必须需要 await asyncio.sleep ，否则上方 task.cancel() 调用无法调度生效
        # This line must be required, otherwise the `task.cancel()` call cannot be scheduled to take effect
        await asyncio.sleep(0)

        tornado.ioloop.IOLoop.current().stop()

    def server_thread():
        from tornado.log import access_log, app_log, gen_log
        access_log.setLevel(logging.ERROR)
        app_log.setLevel(logging.ERROR)
        gen_log.setLevel(logging.ERROR)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        set_ioloop(tornado.ioloop.IOLoop.current())  # to enable bokeh app

        port = 0
        if os.environ.get("PYWEBIO_SCRIPT_MODE_PORT"):
            port = int(os.environ.get("PYWEBIO_SCRIPT_MODE_PORT"))

        server, port = _setup_server(webio_handler=SingleSessionWSHandler, port=port, host='127.0.0.1',
                                     websocket_max_message_size=parse_file_size('200M'))
        tornado.ioloop.IOLoop.current().spawn_callback(partial(wait_to_stop_loop, server=server))

        if "PYWEBIO_SCRIPT_MODE_PORT" not in os.environ:
            tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, '127.0.0.1', port)

        tornado.ioloop.IOLoop.current().start()
        logger.debug('Tornado server exit')

    t = threading.Thread(target=server_thread, name='Tornado-server')
    t.start()

    websocket_conn_opened.wait()
