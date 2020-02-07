import tornado.websocket
import time, json
from collections import defaultdict


class Future:
    def __init__(self):
        self.result = None
        self._callbacks = []

    def add_done_callback(self, fn):
        # todo Future已完成时，立即回调fn
        self._callbacks.append(fn)

    def set_result(self, result):
        self.result = result
        for fn in self._callbacks:
            fn(self)

    def __iter__(self):
        yield self
        return self.result

    __await__ = __iter__  # make compatible with 'await' expression


class Task:
    def __init__(self, coro):
        self.coro = coro
        f = Future()
        f.set_result(None)
        self.step(f)

        self.result = None  # 协程的返回值
        self.on_task_finish = None  # 协程完毕的回调函数

    def step(self, future):
        try:
            # send会进入到coro执行, 即fetch, 直到下次yield
            # next_future 为yield返回的对象
            next_future = self.coro.send(future.result)
            next_future.add_done_callback(self.step)
        except StopIteration as e:
            if len(e.args) == 1:
                self.result = e.args[0]
            if self.on_task_finish:
                self.on_task_finish(self.result)
            return


class Msg:
    mid2callback = defaultdict(list)

    @staticmethod
    def gen_msg_id():
        mid = '%s-%s' % (Global.active_ws.sid, int(time.time()))
        return mid

    @classmethod
    def add_callback(cls, msg_id, callback):
        cls.mid2callback[msg_id].append(callback)

    @classmethod
    def get_callbacks(cls, msg_id):
        return cls.mid2callback[msg_id]

    @classmethod
    def get_callbacks(cls, msg_id):
        return cls.mid2callback[msg_id]

    @classmethod
    def unregister_msg(cls, msg_id):
        del cls.mid2callback[msg_id]


class Global:
    active_ws: "EchoWebSocket"
