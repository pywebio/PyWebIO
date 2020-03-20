import tornado.websocket
from tornado.web import StaticFileHandler
from .session.asyncbased import AsyncBasedSession
from .platform import STATIC_PATH
from .platform.tornado import webio_handler


def run_async(coro_obj):
    AsyncBasedSession.get_current_session().run_async(coro_obj)


def start_ioloop(coro_func, port=8080, debug=True, tornado_app_args=None):
    """
    tornado app arg
        websocket_max_message_size
        ``websocket_ping_interval``, ``websocket_ping_timeout``, and
       ``websocket_max_message_size``.

    """
    handlers = [(r"/io", webio_handler(coro_func)),
                (r"/(.*)", StaticFileHandler, {"path": STATIC_PATH,
                                               'default_filename': 'index.html'})]

    tornado_app_args = tornado_app_args or {}
    app = tornado.web.Application(handlers=handlers, debug=debug, **tornado_app_args)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(port)

    print('Open http://localhost:%s/ in Web browser' % port)

    tornado.ioloop.IOLoop.instance().start()
