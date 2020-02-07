import tornado.websocket
import time, json
from collections import defaultdict
from .framework import Global, Msg, Task
from os.path import abspath, dirname
from tornado.web import StaticFileHandler

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
            self.sid = int(time.time())
            self.coro = coro()

            Global.active_ws = self
            self.task = Task(self.coro)
            self.task.on_task_finish = self.on_task_finish

        def on_task_finish(self, result):
            print('Task finish, return: %s' % result)
            self.close()

        def on_message(self, message):
            print('on_message', message)
            # self.write_message(u"You said: " + message)
            # { msg_id: , data: }
            data = json.loads(message)

            Global.active_ws = self
            callbacks = Msg.get_callbacks(data['msg_id'])
            for c in callbacks:
                c(data['data'])

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
