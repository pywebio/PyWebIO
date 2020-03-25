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
    一个PyWebIO任务会话， 由不同的后端Backend创建并维护

    WebIOSession是不同的后端Backend与协程交互的桥梁：
        后端Backend在接收到用户浏览器的数据后，会通过调用 ``send_client_event`` 来通知会话，进而由Session驱动协程的运行。
        Task内在调用输入输出函数后，会调用 ``send_task_command`` 向会话发送输入输出消息指令， Session将其保存并留给后端Backend处理。

    .. note::
        后端Backend在相应on_session_close时关闭连接时，需要保证会话内的所有消息都传送到了客户端
    """

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

    def __init__(self, coroutine_func, on_task_command=None, on_session_close=None):
        """
        :param coroutine_func: 协程函数
        :param on_task_command: 由协程内发给session的消息的处理函数
        :param on_session_close: 会话结束的处理函数。后端Backend在相应on_session_close时关闭连接时，需要保证会话内的所有消息都传送到了客户端
        """
        self._on_task_command = on_task_command or (lambda _: None)
        self._on_session_close = on_session_close or (lambda: None)
        self.unhandled_task_msgs = []

        self.coros = {}  # coro_task_id -> coro

        self._closed = False
        self.inactive_coro_instances = []  # 待激活的协程实例列表

        self.main_task = Task(coroutine_func(), session=self, on_coro_stop=self._on_main_task_finish)
        self.coros[self.main_task.coro_id] = self.main_task

        self._step_task(self.main_task)

    def _step_task(self, task, result=None):
        task.step(result)
        if task.task_finished and task.coro_id in self.coros:
            # 若task 为main task，则 task.step(result) 结束后，可能task已经结束，self.coros已被清理
            logger.debug('del self.coros[%s]', task.coro_id)
            del self.coros[task.coro_id]

        while self.inactive_coro_instances and not self.main_task.task_finished:
            coro = self.inactive_coro_instances.pop()
            sub_task = Task(coro, session=self)
            self.coros[sub_task.coro_id] = sub_task
            sub_task.step()
            if sub_task.task_finished:
                logger.debug('del self.coros[%s]', sub_task.coro_id)
                del self.coros[sub_task.coro_id]

    def _on_main_task_finish(self):
        self.send_task_command(dict(command='close_session'))
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

        while self.inactive_coro_instances:
            coro = self.inactive_coro_instances.pop()
            coro.close()

    def close(self, no_session_close_callback=False):
        """关闭当前Session

        :param bool no_session_close_callback: 不调用 on_session_close 会话结束的处理函数。
            当 close 是由后端Backend调用时可能希望开启 no_session_close_callback
        """
        self._cleanup()
        self._closed = True
        if not no_session_close_callback:
            self._on_session_close()
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
        put_markdown("发生错误：\n```\n%s\n```" % traceback_msg)

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
        self.inactive_coro_instances.append(coro_obj)

    async def run_asyncio_coroutine(self, coro_obj):
        """若会话线程和运行事件的线程不是同一个线程，需要用 asyncio_coroutine 来运行asyncio中的协程"""
        res = await WebIOFuture(coro=coro_obj)
        return res


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
        self.task_finished = False  # 任务完毕/取消
        self.on_coro_stop = on_coro_stop or (lambda: None)

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
                self.task_finished = True
                logger.debug('Task[%s] finished', self.coro_id)
                self.on_coro_stop()
            except Exception as e:
                self.session.on_task_exception()

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
        logger.debug('Task[%s] closed', self.coro_id)
        self.coro.close()
        while self.pending_futures:
            _, f = self.pending_futures.popitem()
            f.cancel()

        self.task_finished = True

    def __del__(self):
        if not self.task_finished:
            logger.warning('Task[%s] not finished when destroy', self.coro_id)
