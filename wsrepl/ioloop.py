import tornado.websocket
import time, json
from collections import defaultdict, OrderedDict
from .framework import Global, Msg, Task
from os.path import abspath, dirname
from tornado.web import StaticFileHandler
from tornado.gen import coroutine, sleep
from tornado.log import gen_log
import logging

project_dir = dirname(abspath(__file__))


def start_ioloop(coro_func, port=8080):
    class EchoWebSocket(tornado.websocket.WebSocketHandler):

        def check_origin(self, origin):
            return True

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        @coroutine
        def open(self):
            print("WebSocket opened")
            self.set_nodelay(True)
            ############
            self.coros = {}  # coro_id -> coro
            self.callbacks = OrderedDict()  # UI元素时的回调, key -> callback, mark_id
            self.mark2id = {}  # mark_name -> mark_id

            self.inactive_coro_instances = []  # 待激活的协程实例列表
            # self.tornado_coro_instances = []  # 待执行的tornado coro列表

            task = Task(coro_func(), ws=self)
            self.coros[task.coro_id] = task

            yield task.step()
            if task.task_finished:
                gen_log.debug('del self.coros[%s]', task.coro_id)
                del self.coros[task.coro_id]

            yield self.after_step()

        @coroutine
        def after_step(self):
            while self.inactive_coro_instances:
                coro = self.inactive_coro_instances.pop()
                task = Task(coro, ws=self)
                self.coros[task.coro_id] = task
                yield task.step()
                if self.coros[task.coro_id].task_finished:
                    gen_log.debug('del self.coros[%s]', task.coro_id)
                    del self.coros[task.coro_id]
                # yield self.after_step()

            # while self.tornado_coro_instances:
            #     yield self.tornado_coro_instances.pop()

        @coroutine
        def on_message(self, message):
            # print('on_message', message)
            # { event:, coro_id:, data: }
            data = json.loads(message)
            coro_id = data['coro_id']
            coro = self.coros.get(coro_id)
            if not coro_id:
                gen_log.error('coro not found, coro_id:%s', coro_id)
                return

            yield coro.step(data)

            if coro.task_finished:
                gen_log.debug('del self.coros[%s]', coro_id)
                del self.coros[coro_id]

            yield self.after_step()

            if not self.coros:
                self.close()

        def on_close(self):
            print("WebSocket closed")

    handlers = [(r"/test", EchoWebSocket),
                (r"/(.*)", StaticFileHandler,
                 {"path": '%s/html/' % project_dir,
                  'default_filename': 'index.html'})]

    gen_log.setLevel(logging.DEBUG)

    app = tornado.web.Application(handlers=handlers, debug=True)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(port)

    print('Open http://localhost:%s/ in Web browser' % port)

    tornado.ioloop.IOLoop.instance().start()
