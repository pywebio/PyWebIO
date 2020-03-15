import logging
import random
import string
import sys
import time
import traceback
from collections import defaultdict
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class WebIOFuture:
    def __iter__(self):
        result = yield
        return result

    __await__ = __iter__  # make compatible with 'await' expression


class WebIOSession:
    def __init__(self, coro_func, server_msg_listener=None):
        self._server_msg_listener = server_msg_listener or (lambda _: None)
        self.unhandled_server_msgs = []

        self.coros = {}  # coro_id -> coro

        self._closed = False
        self.inactive_coro_instances = []  # 待激活的协程实例列表

        self.main_task = Task(coro_func(), ws=self)
        self.coros[self.main_task.coro_id] = self.main_task

        self._step_task(self.main_task)

    def _step_task(self, task, result=None):
        task.step(result)
        if task.task_finished:
            logger.debug('del self.coros[%s]', task.coro_id)
            del self.coros[task.coro_id]

        while self.inactive_coro_instances:
            coro = self.inactive_coro_instances.pop()
            sub_task = Task(coro, ws=self)
            self.coros[sub_task.coro_id] = sub_task
            sub_task.step()
            if sub_task.task_finished:
                logger.debug('del self.coros[%s]', sub_task.coro_id)
                del self.coros[sub_task.coro_id]

        if self.main_task.task_finished:
            self.close()

    def add_server_msg(self, message):
        self.unhandled_server_msgs.append(message)
        self._server_msg_listener(self)

    def add_client_msg(self, message):
        # data = json.loads(message)
        coro_id = message['coro_id']
        coro = self.coros.get(coro_id)
        if not coro:
            logger.error('coro not found, coro_id:%s', coro_id)
            return

        self._step_task(coro, message)

    def on_coro_error(self):
        from pywebio.output import put_markdown  # todo

        type, value, tb = sys.exc_info()
        tb_len = len(list(traceback.walk_tb(tb)))
        lines = traceback.format_exception(type, value, tb, limit=1 - tb_len)
        traceback_msg = ''.join(lines)
        put_markdown("发生错误：\n```\n%s\n```" % traceback_msg)

    def _cleanup(self):
        for t in self.coros.values():
            t.cancel()
        self.coros = {}  # delete session tasks

        while self.inactive_coro_instances:
            coro = self.inactive_coro_instances.pop()
            coro.close()

    def close(self):
        """关闭当前Session"""
        self._cleanup()
        self._closed = True
        # todo clean

    def closed(self):
        return self._closed


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
        self.task_finished = False  # 任务完毕/取消

        self.coro_id = self.gen_coro_id(self.coro)

        self.pending_futures = {}  # id(future) -> future

        logger.debug('Task[%s] created ', self.coro_id)

    def step(self, result=None):
        future_or_none = None
        with self.ws_context():
            try:
                future_or_none = self.coro.send(result)
            except StopIteration as e:
                if len(e.args) == 1:
                    self.result = e.args[0]
                self.task_finished = True
                logger.debug('Task[%s] finished', self.coro_id)
            except Exception as e:
                self.ws.on_coro_error()

        if not isinstance(future_or_none, WebIOFuture) and future_or_none is not None:
            if not self.ws.closed():
                future_or_none.add_done_callback(self._tornado_future_callback)
                self.pending_futures[id(future_or_none)] = future_or_none

    def _tornado_future_callback(self, future):
        if not future.cancelled():
            del self.pending_futures[id(future)]
            self.step(future.result())

    def cancel(self):
        logger.debug('Task[%s] canceled', self.coro_id)
        self.coro.close()
        while self.pending_futures:
            _, f = self.pending_futures.popitem()
            f.cancel()

        self.task_finished = True

    def __del__(self):
        if not self.task_finished:
            logger.warning('Task[%s] not finished when destroy', self.coro_id)


class Global:
    # todo issue: with 语句可能发生嵌套，导致内层with退出时，将属性置空
    active_ws = None  # type:"WebIOController"
    active_coro_id = None
