import tornado.websocket
import time, json
from collections import defaultdict
from tornado.gen import coroutine, sleep
import random, string
from contextlib import contextmanager
from tornado.log import gen_log
from tornado import ioloop
# from tornado.concurrent import Future


class WebIOFuture:
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
        self.ws = ws
        self.coro = coro
        self.coro_id = None
        self.result = None
        self.task_finished = False  # 协程完毕

        self.coro_id = self.gen_coro_id(self.coro)

        self.pending_futures = {}  # id(future) -> future

        gen_log.debug('Task[%s] __init__ ', self.coro_id)

    def step(self, result=None):
        future_or_none = None
        with self.ws_context():
            try:
                future_or_none = self.coro.send(result)
            except StopIteration as e:
                if len(e.args) == 1:
                    self.result = e.args[0]
                self.task_finished = True
                gen_log.debug('Task[%s] finished', self.coro_id)
            except Exception as e:
                self.ws.on_coro_error()

        if not isinstance(future_or_none, WebIOFuture) and future_or_none is not None:
            if not self.ws.closed():
                future_or_none.add_done_callback(self._tornado_future_callback)
                self.pending_futures[id(future_or_none)] = future_or_none

    def _tornado_future_callback(self, future):
        del self.pending_futures[id(future)]
        self.step(future.result())

    def cancel(self):
        gen_log.debug('Task[%s] canceled', self.coro_id)
        self.coro.close()
        while self.pending_futures:
            _, f = self.pending_futures.popitem()
            f.cancel()

    def __del__(self):
        if not self.task_finished:
            gen_log.warning('Task[%s] not finished when destroy', self.coro_id)


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
    active_ws = None  # type:"EchoWebSocket"
    active_coro_id = None
