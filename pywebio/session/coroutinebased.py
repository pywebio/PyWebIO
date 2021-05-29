import asyncio
import logging
import threading
from contextlib import contextmanager
from functools import partial

from .base import Session
from ..exceptions import SessionNotFoundException, SessionClosedException, SessionException
from ..utils import random_str, isgeneratorfunction, iscoroutinefunction

logger = logging.getLogger(__name__)


class WebIOFuture:
    def __init__(self, coro=None):
        self.coro = coro

    def __iter__(self):
        result = yield self
        return result

    __await__ = __iter__  # make compatible with 'await' expression


class _context:
    current_session = None  # type:"CoroutineBasedSession"
    current_task_id = None


class CoroutineBasedSession(Session):
    """
    基于协程的任务会话

    当主协程任务和会话内所有通过 `run_async` 注册的协程都退出后，会话关闭。
    当用户浏览器主动关闭会话，CoroutineBasedSession.close 被调用， 协程任务和会话内所有通过 `run_async` 注册的协程都被关闭。

    """

    # 运行事件循环的线程id
    # 用于在 CoroutineBasedSession.get_current_session() 判断调用方是否合法
    # Tornado backend时，在创建第一个CoroutineBasedSession时初始化
    # Flask backend时，在platform.flaskrun_event_loop()时初始化
    event_loop_thread_id = None

    @classmethod
    def get_current_session(cls) -> "CoroutineBasedSession":
        if _context.current_session is None or cls.event_loop_thread_id != threading.current_thread().ident:
            raise SessionNotFoundException("No session found in current context!")

        if _context.current_session.closed():
            raise SessionClosedException

        return _context.current_session

    @staticmethod
    def get_current_task_id():
        if _context.current_task_id is None:
            raise RuntimeError("No current task found in context!")
        return _context.current_task_id

    def __init__(self, target, session_info, on_task_command=None, on_session_close=None):
        """
        :param target: 协程函数
        :param on_task_command: 由协程内发给session的消息的处理函数
        :param on_session_close: 会话结束的处理函数。后端Backend在相应on_session_close时关闭连接时，需要保证会话内的所有消息都传送到了客户端
        """
        assert iscoroutinefunction(target) or isgeneratorfunction(target), ValueError(
            "CoroutineBasedSession accept coroutine function or generator function as task function")

        super().__init__(session_info)

        cls = type(self)

        self._on_task_command = on_task_command or (lambda _: None)
        self._on_session_close = on_session_close or (lambda: None)

        # 当前会话未被Backend处理的消息
        self.unhandled_task_msgs = []

        # 在创建第一个CoroutineBasedSession时 event_loop_thread_id 还未被初始化
        # 则当前线程即为运行 event loop 的线程
        if cls.event_loop_thread_id is None:
            cls.event_loop_thread_id = threading.current_thread().ident

        # 会话内的协程任务
        self.coros = {}  # coro_task_id -> Task()

        self._closed = False

        # 当前会话未结束运行(已创建和正在运行的)的协程数量。当 _alive_coro_cnt 变为 0 时，会话结束。
        self._alive_coro_cnt = 1

        main_task = Task(target(), session=self, on_coro_stop=self._on_task_finish)
        self.coros[main_task.coro_id] = main_task

        self._step_task(main_task)

    def _step_task(self, task, result=None):
        asyncio.get_event_loop().call_soon_threadsafe(partial(task.step, result))

    def _on_task_finish(self, task: "Task"):
        self._alive_coro_cnt -= 1

        if task.coro_id in self.coros:
            logger.debug('del self.coros[%s]', task.coro_id)
            del self.coros[task.coro_id]

        if self._alive_coro_cnt <= 0 and not self.closed():
            self.send_task_command(dict(command='close_session'))
            self._on_session_close()
            self.close()

    def send_task_command(self, command):
        """向会话发送来自协程内的消息

        :param dict command: 消息
        """
        if self.closed():
            raise SessionClosedException()
        self.unhandled_task_msgs.append(command)
        self._on_task_command(self)

    async def next_client_event(self):
        # 函数开始不需要判断 self.closed()
        # 如果会话关闭，对 get_current_session().next_client_event() 的调用会抛出SessionClosedException
        return await WebIOFuture()

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
        for t in list(self.coros.values()):  # t.close() may cause self.coros changed size
            t.step(SessionClosedException, throw_exp=True)
            t.close()
        self.coros = {}  # delete session tasks

    def close(self, nonblock=False):
        """关闭当前Session。由Backend调用"""
        if self.closed():
            return

        super().close()

        self._cleanup()

    def register_callback(self, callback, mutex_mode=False):
        """ 向Session注册一个回调函数，返回回调id

        :type callback: Callable or Coroutine
        :param callback: 回调函数. 函数签名为 ``callback(data)``. ``data`` 参数为回调事件的值
        :param bool mutex_mode: 互斥模式。若为 ``True`` ，则在运行回调函数过程中，无法响应同一组件（callback_id相同）的新点击事件，仅当 ``callback`` 为协程函数时有效
        :return str: 回调id.
        """

        async def callback_coro():
            while True:
                try:
                    event = await self.next_client_event()
                except SessionClosedException:
                    return

                assert event['event'] == 'callback'
                coro = None
                if iscoroutinefunction(callback):
                    coro = callback(event['data'])
                elif isgeneratorfunction(callback):
                    coro = asyncio.coroutine(callback)(event['data'])
                else:
                    try:
                        res = callback(event['data'])
                        if asyncio.iscoroutine(res):
                            coro = res
                        else:
                            del res  # `res` maybe pywebio.io_ctrl.Output, so need release `res`
                    except Exception:
                        self.on_task_exception()

                if coro is not None:
                    if mutex_mode:
                        await coro
                    else:
                        self.run_async(coro)

        cls = type(self)
        callback_task = Task(callback_coro(), cls.get_current_session())
        # Activate task
        # Don't callback.step(), it will result in recursive calls to step()
        # todo: integrate with inactive_coro_instances
        callback_task.coro.send(None)
        cls.get_current_session().coros[callback_task.coro_id] = callback_task

        return callback_task.coro_id

    def run_async(self, coro_obj):
        """异步运行协程对象。可以在协程内调用 PyWebIO 交互函数

        :param coro_obj: 协程对象
        :return: An instance of  `TaskHandler` is returned, which can be used later to close the task.
        """
        assert asyncio.iscoroutine(coro_obj), '`run_async()` only accept coroutine object'

        self._alive_coro_cnt += 1

        task = Task(coro_obj, session=self, on_coro_stop=self._on_task_finish)
        self.coros[task.coro_id] = task
        asyncio.get_event_loop().call_soon_threadsafe(task.step)
        return task.task_handle()

    async def run_asyncio_coroutine(self, coro_obj):
        """若会话线程和运行事件的线程不是同一个线程，需要用 asyncio_coroutine 来运行asyncio中的协程"""
        assert asyncio.iscoroutine(coro_obj), '`run_asyncio_coroutine()` only accept coroutine object'

        res = await WebIOFuture(coro=coro_obj)
        return res


class TaskHandler:
    """The handler of coroutine task

    See also: `run_async() <pywebio.session.run_async>`
    """

    def __init__(self, close, closed):
        self._close = close
        self._closed = closed

    def close(self):
        """Close the coroutine task."""
        return self._close()

    def closed(self) -> bool:
        """Returns a bool stating whether the coroutine task is closed. """
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
        """生成协程id"""
        name = 'coro'
        if hasattr(coro, '__name__'):
            name = coro.__name__

        return '%s-%s' % (name, random_str(10))

    def __init__(self, coro, session: CoroutineBasedSession, on_coro_stop=None):
        """
        :param coro: 协程对象
        :param session: 创建该Task的会话实例
        :param on_coro_stop: 任务结束(正常结束或外部调用Task.close)时运行的回调
        """
        self.session = session
        self.coro = coro
        self.coro_id = None
        self.result = None
        self.task_closed = False  # 任务完毕/取消
        self.on_coro_stop = on_coro_stop or (lambda _: None)

        self.coro_id = self.gen_coro_id(self.coro)

        self.pending_futures = {}  # id(future) -> future

        logger.debug('Task[%s] created ', self.coro_id)

    def step(self, result=None, throw_exp=False):
        """激活协程

        :param any result: 向协程传入的数据
        :param bool throw_exp: 是否向协程引发异常，为 True 时， result 参数为相应的异常对象
        """
        coro_yield = None
        with self.session_context():
            try:
                if throw_exp:
                    coro_yield = self.coro.throw(result)
                else:
                    coro_yield = self.coro.send(result)
            except StopIteration as e:
                if len(e.args) == 1:
                    self.result = e.args[0]
                self.task_closed = True
                logger.debug('Task[%s] finished', self.coro_id)
                self.on_coro_stop(self)
            except Exception as e:
                if not isinstance(e, SessionException):
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
            future.add_done_callback(self._wakeup)
            self.pending_futures[id(future)] = future

    def _wakeup(self, future):
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
            logger.warning('Task[%s] was destroyed but it is pending!', self.coro_id)

    def task_handle(self):
        handle = TaskHandler(close=self.close, closed=lambda: self.task_closed)
        return handle
