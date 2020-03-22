import asyncio
import json
import logging
import webbrowser

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.websocket
from tornado.web import StaticFileHandler
from . import STATIC_PATH
from ..session import AsyncBasedSession, ThreadBasedWebIOSession, get_session_implement
from ..utils import get_free_port, wait_host_port

logger = logging.getLogger(__name__)


def webio_handler(task_func):
    class WSHandler(tornado.websocket.WebSocketHandler):

        def check_origin(self, origin):
            return True

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        def send_msg_to_client(self, controller: AsyncBasedSession):
            for msg in controller.get_task_messages():
                self.write_message(json.dumps(msg))

        def open(self):
            logger.debug("WebSocket opened")
            self.set_nodelay(True)

            self._close_from_session = False  # 是否从session中关闭连接

            if get_session_implement() is AsyncBasedSession:
                self.controller = AsyncBasedSession(task_func, on_task_message=self.send_msg_to_client,
                                                    on_session_close=self.close)
            else:
                self.controller = ThreadBasedWebIOSession(task_func, on_task_message=self.send_msg_to_client,
                                                          on_session_close=self.close_from_session,
                                                          loop=asyncio.get_event_loop())

        def on_message(self, message):
            data = json.loads(message)
            self.controller.send_client_event(data)

        def close_from_session(self):
            self._close_from_session = True
            self.close()

        def on_close(self):
            if not self._close_from_session:
                self.controller.close(no_session_close_callback=True)
            logger.debug("WebSocket closed")

    return WSHandler


async def open_webbrowser_on_server_started(host, port):
    url = 'http://%s:%s' % (host, port)
    is_open = await wait_host_port(host, port, duration=5, delay=0.5)
    if is_open:
        logger.info('Openning %s' % url)
        webbrowser.open(url)
    else:
        logger.error('Open %s failed.' % url)


def start_server(target, port=0, host='', debug=True,
                 auto_open_webbrowser=False,
                 websocket_max_message_size=None,
                 websocket_ping_interval=None,
                 websocket_ping_timeout=None,
                 **tornado_app_settings):
    """Start a Tornado server to serve `target` function

    :param target: task function. It's a coroutine function is use AsyncBasedSession or
        a simple function is use ThreadBasedWebIOSession.
    :param port: server bind port. set ``0`` to find a free port number to use
    :param host: server bind host. ``host`` may be either an IP address or hostname.  If it's a hostname,
        the server will listen on all IP addresses associated with the name.
        set empty string or to listen on all available interfaces.
    :param bool debug: Tornado debug mode
    :param bool auto_open_webbrowser: auto open web browser when server started
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
    :return:
    """
    kwargs = locals()
    app_options = ['debug', 'websocket_max_message_size', 'websocket_ping_interval', 'websocket_ping_timeout']
    for opt in app_options:
        if kwargs[opt] is not None:
            tornado_app_settings[opt] = kwargs[opt]

    if port == 0:
        port = get_free_port()

    print('Listen on %s:%s' % (host or '0.0.0.0', port))

    handlers = [(r"/io", webio_handler(target)),
                (r"/(.*)", StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'})]

    app = tornado.web.Application(handlers=handlers, **tornado_app_settings)
    app.listen(port, address=host)

    if auto_open_webbrowser:
        tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, host or '0.0.0.0', port)
    tornado.ioloop.IOLoop.current().start()
