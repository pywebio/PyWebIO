import json
from collections import OrderedDict

import tornado
import tornado.websocket
from tornado.gen import coroutine
from tornado.log import gen_log

from wsrepl.framework import Task

from wsrepl import project_dir

STATIC_PATH = '%s/html' % project_dir


def ws_handler(coro_func):
    class WSHandler(tornado.websocket.WebSocketHandler):

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

            self._closed = False
            self.inactive_coro_instances = []  # 待激活的协程实例列表

            self.main_task = Task(coro_func(), ws=self)
            self.coros[self.main_task.coro_id] = self.main_task

            self.step_task(self.main_task)

        def step_task(self, task, result=None):
            task.step(result)
            if task.task_finished:
                gen_log.debug('del self.coros[%s]', task.coro_id)
                del self.coros[task.coro_id]

            while self.inactive_coro_instances:
                coro = self.inactive_coro_instances.pop()
                task = Task(coro, ws=self)
                self.coros[task.coro_id] = task
                task.step()
                if self.coros[task.coro_id].task_finished:
                    gen_log.debug('del self.coros[%s]', task.coro_id)
                    del self.coros[task.coro_id]

            if self.main_task.task_finished:
                for t in self.coros:
                    t.cancel()
                self.close()

        def on_message(self, message):
            # print('on_message', message)
            data = json.loads(message)
            coro_id = data['coro_id']
            coro = self.coros.get(coro_id)
            if not coro_id:
                gen_log.error('coro not found, coro_id:%s', coro_id)
                return

            self.step_task(coro, data)

        def on_close(self):
            self._closed = True
            print("WebSocket closed")

        def closed(self):
            return self._closed

    return WSHandler
