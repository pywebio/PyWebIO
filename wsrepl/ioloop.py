import logging

import tornado.websocket
from tornado.log import gen_log
from tornado.web import StaticFileHandler

from wsrepl.platform.tornado import ws_handler, STATIC_PATH
from wsrepl import project_dir


def start_ioloop(coro_func, port=8080, debug=True, tornado_app_args=None):
    handlers = [(r"/test", ws_handler(coro_func)),
                (r"/(.*)", StaticFileHandler, {"path": STATIC_PATH,
                                               'default_filename': 'index.html'})]

    gen_log.setLevel(logging.DEBUG)
    tornado_app_args = tornado_app_args or {}
    app = tornado.web.Application(handlers=handlers, debug=debug, **tornado_app_args)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(port)

    print('Open http://localhost:%s/ in Web browser' % port)

    tornado.ioloop.IOLoop.instance().start()
