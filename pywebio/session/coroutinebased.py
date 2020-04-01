import asyncio
import inspect
import logging
import sys
import traceback
from contextlib import contextmanager

from .base import AbstractSession
from ..exceptions import SessionNotFoundException
from ..utils import random_str

logger = logging.getLogger(__name__)


class WebIOFuture:
    def __init__(self, coro=None):
        self.coro = coro

    def __iter__(self):
        result = yield self
        return result

    __await__ = __iter__  # make compatible with 'await' expression


class _context:
    current_session = None  # type:"AsyncBasedSession"
    current_task_id = None


class CoroutineBasedSession(AbstractSession):
    """
    基于协程的任务会话

    当主协程任务和会话内所有通过 `run_async` 注册的协程都退出后，会话关闭。
    当用户浏览器主动关闭会话，CoroutineBasedSession.close 被调用， 协程任务和会话内所有通过 `run_async` 注册的协程都被关闭。
    """

    _active_session_cnt = 0

    @classmethod
    def active_session_count(cls):
        return cls._active_session_cnt

    @staticmethod
    def get_current_session() -> "CoroutineBasedSession":
        if _context.current_session is None:
            raise SessionNotFoundException("No current found in context!")
        return _context.current_session

    @staticmethod
    def get_current_task_id():
        if _context.current_task_id is None:
            raise RuntimeError("No current task found in context!")
        return _context.current_task_id

    def __init__(self, target, on_task_command=None, on_session_close=None):
        """
        :param target: 协程函数
        :param on_task_command: 由协程内发给session的消息的处理函数
        :param on_session_close: 会话结束的处理函数。后端Backend在相应on_session_close时关闭连接时，需要保证会话内的所有消息都传送到了客户端
        """
        assert asyncio.iscoroutinefunction(target) or inspect.isgeneratorfunction(target), ValueError(
            "CoroutineBasedSession accept coroutine function or generator function as task function")

        CoroutineBasedSession._active_session_cnt += 1

        self._on_task_command = on_task_command or (lambda _: None)
        self._on_session_close = on_session_close or (lambda: None)
        self.unhandled_task_msgs = []

        self.coros = {}  # coro_task_id -> coro

        self._closed = False
        self._not_closed_coro_cnt = 1  # 当前会话未结束运行的协程数量。当 self._not_closed_coro_cnt == 0 时，会话结束。

        main_task = Task(target(), session=self, on_coro_stop=self._on_task_finish)
        self.coros[main_task.coro_id] = main_task

        self._step_task(main_task)

    def _step_task(self, task, result=None):
        task.step(result)

    def _on_task_finish(self, task: "Task"):
        self._not_closed_coro_cnt -= 1

        if task.coro_id in self.coros:
            logger.debug('del self.coros[%s]', task.coro_id)
            del self.coros[task.coro_id]

        if self._not_closed_coro_cnt <= 0:
            self.send_task_command(dict(command='close_session'))
            self._on_session_close()
            self.close()

    def send_task_command(self, command):
        """向会话发送来自协程内的消息

        :param dict command: 消息
        """
        self.unhandled_task_msgs.append(command)
        self._on_task_command(self)

    async def next_client_event(self):
        res = await WebIOFuture()
        return res

    def send_client_event(self, event):
        """向会话发送来自用户浏览器的事件️

        :param dict event: 事件️消息
        """
        coro_id = event['task_id']
        coro = self.coros.get(coro_id)
        if not coro:
            logger.error('coro not found, coro_id:%s', coro_id)
            return

        self._step_task(coro, event)

    def get_task_commands(self):
        msgs = self.unhandled_task_msgs
        self.unhandled_task_msgs = []
        return msgs

    def _cleanup(self):
        for t in self.coros.values():
            t.close()
        self.coros = {}  # delete session tasks
        CoroutineBasedSession._active_session_cnt -= 1

    def close(self):
        """关闭当前Session。由Backend调用"""
        if self._closed:
            return
        self._closed = True
        self._cleanup()
        # todo clean

    def closed(self):
        return self._closed

    def on_task_exception(self):
        from ..output import put_markdown  # todo
        logger.exception('Error in coroutine executing')
        type, value, tb = sys.exc_info()
        tb_len = len(list(traceback.walk_tb(tb)))
        lines = traceback.format_exception(type, value, tb, limit=1 - tb_len)
        traceback_msg = ''.join(lines)
        try:
            put_markdown("发生错误：\n```\n%s\n```" % traceback_msg)
        except:
            pass

    def register_callback(self, callback, mutex_mode=False):
        """ 向Session注册一个回调函数，返回回调id

        :type callback: Callable or Coroutine
        :param callback: 回调函数. 可以是普通函数或者协程函数. 函数签名为 ``callback(data)``.
        :param bool mutex_mode: 互斥模式。若为 ``True`` ，则在运行回调函数过程中，无法响应同一组件的新点击事件，仅当 ``callback`` 为协程函数时有效
        :return str: 回调id.
            CoroutineBasedSession 保证当收到前端发送的事件消息 ``{event: "callback"，coro_id: 回调id, data:...}`` 时，
            ``callback`` 回调函数被执行， 并传入事件消息中的 ``data`` 字段值作为参数
        """

        async def callback_coro():
            while True:
                event = await self.next_client_event()
                assert event['event'] == 'callback'
                coro = None
                if asyncio.iscoroutinefunction(callback):
                    coro = callback(event['data'])
                elif inspect.isgeneratorfunction(callback):
                    coro = asyncio.coroutine(callback)(event['data'])
                else:
                    try:
                        callback(event['data'])
                    except:
                        CoroutineBasedSession.get_current_session().on_task_exception()

                if coro is not None:
                    if mutex_mode:
                        await coro
                    else:
                        self.run_async(coro)

        callback_task = Task(callback_coro(), CoroutineBasedSession.get_current_session())
        callback_task.coro.send(None)  # 激活，Non't callback.step() ,导致嵌套调用step  todo 与inactive_coro_instances整合
        CoroutineBasedSession.get_current_session().coros[callback_task.coro_id] = callback_task

        return callback_task.coro_id

    def run_async(self, coro_obj):
        """异步运行协程对象。可以在协程内调用 PyWebIO 交互函数

        :param coro_obj: 协程对象
        :return: An instance of  `TaskHandle` is returned, which can be used later to close the task.
        """
        self._not_closed_coro_cnt += 1

        task = Task(coro_obj, session=self, on_coro_stop=self._on_task_finish)
        self.coros[task.coro_id] = task
        asyncio.get_event_loop().call_soon(task.step)
        return task.task_handle()

    async def run_asyncio_coroutine(self, coro_obj):
        """若会话线程和运行事件的线程不是同一个线程，需要用 asyncio_coroutine 来运行asyncio中的协程"""
        res = await WebIOFuture(coro=coro_obj)
        return res


class TaskHandle:

    def __init__(self, close, closed):
        self._close = close
        self._closed = closed

    def close(self):
        """关闭任务"""
        return self._close()

    def closed(self):
        """返回任务是否关闭"""
        return self._closed()


class Task:

    @contextmanager
    def session_context(self):
        """
        >>> with session_context():
        ...     res = self.coros[-1].send(data)
        """

        # todo issue: with 语句可能发生嵌套，导致内层with退出时，将属性置空
        _context.current_session = self.session
        _context.current_task_id = self.coro_id
        try:
            yield
        finally:
            _context.current_session = None
            _context.current_task_id = None

    @staticmethod
    def gen_coro_id(coro=None):
        name = 'coro'
        if hasattr(coro, '__name__'):
            name = coro.__name__

        return '%s-%s' % (name, random_str(10))

    def __init__(self, coro, session: CoroutineBasedSession, on_coro_stop=None):
        self.session = session
        self.coro = coro
        self.coro_id = None
        self.result = None
        self.task_closed = False  # 任务完毕/取消
        self.on_coro_stop = on_coro_stop or (lambda _: None)

        self.coro_id = self.gen_coro_id(self.coro)

        self.pending_futures = {}  # id(future) -> future

        logger.debug('Task[%s] created ', self.coro_id)

    def step(self, result=None):
        coro_yield = None
        with self.session_context():
            try:
                coro_yield = self.coro.send(result)
            except StopIteration as e:
                if len(e.args) == 1:
                    self.result = e.args[0]
                self.task_closed = True
                logger.debug('Task[%s] finished', self.coro_id)
                self.on_coro_stop(self)
            except Exception as e:
                self.session.on_task_exception()
                self.task_closed = True
                self.on_coro_stop(self)

        future = None
        if isinstance(coro_yield, WebIOFuture):
            if coro_yield.coro:
                future = asyncio.run_coroutine_threadsafe(coro_yield.coro, asyncio.get_event_loop())
        elif coro_yield is not None:
            future = coro_yield
        if not self.session.closed() and hasattr(future, 'add_done_callback'):
            future.add_done_callback(self._tornado_future_callback)
            self.pending_futures[id(future)] = future

    def _tornado_future_callback(self, future):
        if not future.cancelled():
            del self.pending_futures[id(future)]
            self.step(future.result())

    def close(self):
        if self.task_closed:
            return

        logger.debug('Task[%s] closed', self.coro_id)
        self.coro.close()
        while self.pending_futures:
            _, f = self.pending_futures.popitem()
            f.cancel()

        self.task_closed = True
        self.on_coro_stop(self)

    def __del__(self):
        if not self.task_closed:
            logger.warning('Task[%s] not finished when destroy', self.coro_id)

    def task_handle(self):
        handle = TaskHandle(close=self.close, closed=lambda: self.task_closed)
        return handle
