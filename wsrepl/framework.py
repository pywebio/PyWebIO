import tornado.websocket
import time, json
from collections import defaultdict
from tornado.gen import coroutine, sleep
import random, string
from contextlib import contextmanager


class Future:

    def __iter__(self):
        result = yield
        return result

    __await__ = __iter__  # make compatible with 'await' expression


class Task:
    @contextmanager
    def ws_context(self):
        """
        >>> with ws_context():
        ...     res = self.coros[-1].send(data)
        """
        Global.active_ws = self.ws
        Global.active_coro_id = self.coro_id
        try:
            yield
        finally:
            Global.active_ws = None
            Global.active_coro_id = None

    @staticmethod
    def gen_coro_id(coro=None):
        name = 'coro'
        if hasattr(coro, '__name__'):
            name = coro.__name__

        random_str = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
        return '%s-%s' % (name, random_str)

    def __init__(self, coro, ws):
        print('into Task __init__ `', coro, ws)
        self.ws = ws
        self.coro = coro
        self.coro_id = None
        self.result = None
        self.task_finished = False  # 协程完毕

        self.coro_id = self.gen_coro_id(self.coro)

        # todo issue: 激活协程后，写成的返回值可能是tornado coro，需要执行
        with self.ws_context():
            res = self.coro.send(None)  # 激活协程

        if res is not None:  # todo 执行完，还需要获取结果，coro.send(res)
            self.ws.tornado_coro_instances.append(res)

    def step(self, result):
        try:
            with self.ws_context():
                res = self.coro.send(result)
            return res
        except StopIteration as e:
            if len(e.args) == 1:
                self.result = e.args[0]

            self.task_finished = Task

            # raise


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
    # todo issue: with 语句可能发生嵌套，导致内层with退出时，将属性置空
    active_ws: "EchoWebSocket" = None
    active_coro_id = None
