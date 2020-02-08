import tornado.websocket
import time, json
from collections import defaultdict, OrderedDict
from .framework import Global, Msg, Task
from os.path import abspath, dirname
from tornado.web import StaticFileHandler
from tornado.gen import coroutine,sleep

project_dir = dirname(abspath(__file__))


def start_ioloop(coro, port=8080):
    class EchoWebSocket(tornado.websocket.WebSocketHandler):
        def check_origin(self, origin):
            return True

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        def open(self):
            print("WebSocket opened")
            self.set_nodelay(True)
            ############

            self.coros = [coro()]
            self.callbacks = OrderedDict()  # UI元素时的回调, key -> callback, mark_id
            self.mark2id = {}  # 锚点 -> id

            Global.active_ws = self
            next(self.coros[-1])

        @coroutine
        def on_message(self, message):
            print('on_message', message)
            # { event: , data: }
            data = json.loads(message)
            try:
                Global.active_ws = self
                res = self.coros[-1].send(data)
                while res is not None:
                    print('get not none form coro ', res)
                    yield res
                    Global.active_ws = self
                    res = self.coros[-1].send(data)

            except StopIteration:
                self.close()

        def on_close(self):
            print("WebSocket closed")

    handlers = [(r"/test", EchoWebSocket),
                (r"/(.*)", StaticFileHandler,
                 {"path": '%s/html/' % project_dir,
                  'default_filename': 'index.html'})]

    app = tornado.web.Application(handlers=handlers, debug=True)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(port)

    print('Open http://localhost:%s/ in Web browser' % port)

    tornado.ioloop.IOLoop.instance().start()
