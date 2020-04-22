import logging
import queue
import sys
import threading
import traceback
from functools import wraps

from .base import AbstractSession
from ..exceptions import SessionNotFoundException, SessionClosedException, SessionException
from ..utils import random_str, LimitedSizeQueue, isgeneratorfunction, iscoroutinefunction, catch_exp_call

logger = logging.getLogger(__name__)

"""
基于线程的会话实现

主任务线程退出后，连接关闭，但不会清理主任务线程产生的其他线程

客户端连接关闭后，后端线程不会退出，但是再次调用输入输出函数会引发异常
todo: thread 重名
"""


# todo 线程安全
class ThreadBasedSession(AbstractSession):
    thread2session = {}  # thread_id -> session

    unhandled_task_mq_maxsize = 1000
    event_mq_maxsize = 100
    callback_mq_maxsize = 100

    _active_session_cnt = 0

    @classmethod
    def active_session_count(cls):
        return cls._active_session_cnt

    @classmethod
    def get_current_session(cls) -> "ThreadBasedSession":
        curr = id(threading.current_thread())
        session = cls.thread2session.get(curr)
        if session is None:
            raise SessionNotFoundException(
                "Can't find current session. Maybe session closed. Did you forget to use `register_thread` ?")
        return session

    @classmethod
    def get_current_task_id(cls):
        return cls._get_task_id(threading.current_thread())

    @staticmethod
    def _get_task_id(thread: threading.Thread):
        tname = getattr(thread, '_target', 'task')
        tname = getattr(tname, '__name__', tname)
        return '%s-%s' % (tname, id(thread))

    def __init__(self, target, on_task_command=None, on_session_close=None, loop=None):
        """
        :param target: 会话运行的函数
        :param on_task_command: 当Task内发送Command给session的时候触发的处理函数
        :param on_session_close: 会话结束的处理函数
        :param loop: 事件循环。若 on_task_command 或者 on_session_close 中有调用使用asyncio事件循环的调用，
            则需要事件循环实例来将回调在事件循环的线程中执行
        """
        assert (not iscoroutinefunction(target)) and (not isgeneratorfunction(target)), ValueError(
            "ThreadBasedSession only accept a simple function as task function, "
            "not coroutine function or generator function. ")

        ThreadBasedSession._active_session_cnt += 1

        self._on_task_command = on_task_command or (lambda _: None)
        self._on_session_close = on_session_close or (lambda: None)
        self._loop = loop

        # 会话结束时运行的函数
        self.deferred_functions = []

        self.threads = []  # 注册到当前会话的线程集合
        self.unhandled_task_msgs = LimitedSizeQueue(maxsize=self.unhandled_task_mq_maxsize)

        self.task_mqs = {}  # task_id -> event msg queue
        self._closed = False

        # 用于实现回调函数的注册
        self.callback_mq = None
        self.callback_thread = None
        self.callbacks = {}  # callback_id -> (callback_func, is_mutex)

        self._start_main_task(target)

    def _start_main_task(self, target):

        @wraps(target)
        def main_task(target):
            try:
                target()
            except Exception as e:
                if not isinstance(e, SessionException):
                    self.on_task_exception()
            finally:
                for t in self.threads:
                    if t.is_alive() and t is not threading.current_thread():
                        t.join()
                try:
                    self.send_task_command(dict(command='close_session'))
                except SessionClosedException:
                    pass
                self._trigger_close_event()
                self.close()

        thread = threading.Thread(target=main_task, kwargs=dict(target=target),
                                  daemon=True, name='main_task')
        self.register_thread(thread)

        thread.start()

    def send_task_command(self, command):
        """向会话发送来自协程内的消息

        :param dict command: 消息
        """
        if self.closed():
            raise SessionClosedException()

        self.unhandled_task_msgs.put(command)

        if self._loop:
            self._loop.call_soon_threadsafe(self._on_task_command, self)
        else:
            self._on_task_command(self)

    def next_client_event(self):
        # 函数开始不需要判断 self.closed()
        # 如果会话关闭，对 get_current_session().next_client_event() 的调用会抛出SessionNotFoundException

        task_id = self.get_current_task_id()
        event_mq = self.get_current_session().task_mqs.get(task_id)
        event = event_mq.get()
        if event is None:
            raise SessionClosedException
        return event

    def send_client_event(self, event):
        """向会话发送来自用户浏览器的事件️

        :param dict event: 事件️消息
        """
        task_id = event['task_id']
        mq = self.task_mqs.get(task_id)
        if not mq and task_id in self.callbacks:
            mq = self.callback_mq

        if not mq:
            logger.error('event_mqs not found, task_id:%s', task_id)
            return

        mq.put(event)

    def get_task_commands(self):
        return self.unhandled_task_msgs.get()

    def _trigger_close_event(self):
        """触发Backend on_session_close callback"""
        if self._loop:
            self._loop.call_soon_threadsafe(self._on_session_close)
        else:
            self._on_session_close()

    def _cleanup(self):

        self.unhandled_task_msgs.wait_empty(8)
        if not self.unhandled_task_msgs.empty():
            logger.debug("Unhandled task messages when session close:%s", self.unhandled_task_msgs.get())
            raise RuntimeError('There are unhandled task messages when session close!')

        for t in self.threads:
            del ThreadBasedSession.thread2session[id(t)]

        if self.callback_mq is not None:  # 回调功能已经激活
            self.callback_mq.put(None)  # 结束回调线程

        for mq in self.task_mqs.values():
            mq.put(None)  # 消费端接收到None消息会抛出SessionClosedException异常

        self.task_mqs = {}

        ThreadBasedSession._active_session_cnt -= 1

    def close(self):
        """关闭当前Session。由Backend调用"""
        # todo self._closed 会有竞争条件
        if self._closed:
            return
        self._closed = True

        self._cleanup()

        self.deferred_functions.reverse()
        while self.deferred_functions:
            func = self.deferred_functions.pop()
            catch_exp_call(func, logger)

    def closed(self):
        return self._closed

    def on_task_exception(self):
        from ..output import put_markdown  # todo
        logger.exception('Error in thread executing')
        type, value, tb = sys.exc_info()
        tb_len = len(list(traceback.walk_tb(tb)))
        lines = traceback.format_exception(type, value, tb, limit=1 - tb_len)
        traceback_msg = ''.join(lines)
        try:
            put_markdown("发生错误：\n```\n%s\n```" % traceback_msg)
        except:
            pass

    def _activate_callback_env(self):
        """激活回调功能

        ThreadBasedSession 的回调实现原理是：创建一个单独的线程用于接收回调事件，进而调用相关的回调函数。
        当用户Task中并没有使用到回调功能时，不必开启此线程，可以节省资源
        """

        if self.callback_mq is not None:  # 回调功能已经激活
            return

        self.callback_mq = queue.Queue(maxsize=self.callback_mq_maxsize)
        self.callback_thread = threading.Thread(target=self._dispatch_callback_event,
                                                daemon=True, name='callback-' + random_str(10))
        # self.register_thread(self.callback_thread)
        self.thread2session[id(self.callback_thread)] = self  # 用于在线程内获取会话
        self.callback_thread.start()
        logger.debug('Callback thread start')

    def _dispatch_callback_event(self):
        while not self.closed():
            event = self.callback_mq.get()
            if event is None:  # 结束信号
                logger.debug('Callback thread exit')
                break

            callback_info = self.callbacks.get(event['task_id'])
            if not callback_info:
                logger.error("No callback for callback_id:%s", event['task_id'])
                return
            callback, mutex = callback_info

            @wraps(callback)
            def run(callback):
                try:
                    callback(event['data'])
                except:
                    # 子类可能会重写 get_current_session ，所以不要用 ThreadBasedSession.get_current_session 来调用
                    self.get_current_session().on_task_exception()

            if mutex:
                run(callback)
            else:
                t = threading.Thread(target=run, kwargs=dict(callback=callback),
                                     daemon=True)
                self.register_thread(t)
                t.start()

    def register_callback(self, callback, serial_mode=False):
        """ 向Session注册一个回调函数，返回回调id

        Session需要保证当收到前端发送的事件消息 ``{event: "callback"，task_id: 回调id, data:...}`` 时，
        ``callback`` 回调函数被执行， 并传入事件消息中的 ``data`` 字段值作为参数

        :param bool serial_mode: 串行模式模式。若为 ``True`` ，则对于同一组件的点击事件，串行执行其回调函数
        """
        assert (not iscoroutinefunction(callback)) and (not isgeneratorfunction(callback)), ValueError(
            "In ThreadBasedSession.register_callback, `callback` must be a simple function, "
            "not coroutine function or generator function. ")

        self._activate_callback_env()
        callback_id = 'CB-%s-%s' % (getattr(callback, '__name__', ''), random_str(10))
        self.callbacks[callback_id] = (callback, serial_mode)
        return callback_id

    def register_thread(self, t: threading.Thread):
        """将线程注册到当前会话，以便在线程内调用 pywebio 交互函数。
        会话会一直保持直到所有通过 `register_thread` 注册的线程以及当前会话的主任务线程退出

        :param threading.Thread thread: 线程对象
        """
        self.threads.append(t)  # 保存 registered thread，用于主任务线程退出后等待注册线程结束
        self.thread2session[id(t)] = self  # 用于在线程内获取会话
        event_mq = queue.Queue(maxsize=self.event_mq_maxsize)  # 线程内的用户事件队列
        self.task_mqs[self._get_task_id(t)] = event_mq

    def defer_call(self, func):
        """设置会话结束时调用的函数。可以用于资源清理。"""
        self.deferred_functions.append(func)


class ScriptModeSession(ThreadBasedSession):
    """Script mode的会话实现"""

    @classmethod
    def get_current_session(cls) -> "ScriptModeSession":
        if cls.instance is None:
            raise SessionNotFoundException("Can't find current session. It might be a bug.")
        if cls.instance.closed():
            raise SessionClosedException()
        return cls.instance

    @classmethod
    def get_current_task_id(cls):
        task_id = super().get_current_task_id()
        session = cls.get_current_session()
        if task_id not in session.task_mqs:
            session.register_thread(threading.current_thread())
        return task_id

    instance = None

    def __init__(self, thread, on_task_command=None, loop=None):
        """
        :param on_task_command: 会话结束的处理函数。后端Backend在相应on_session_close时关闭连接时，
            需要保证会话内的所有消息都传送到了客户端
        :param loop: 事件循环。若 on_task_command 或者on_session_close中有调用使用asyncio事件循环的调用，
            则需要事件循环实例来将回调在事件循环的线程中执行
        """
        if ScriptModeSession.instance is not None:
            raise RuntimeError("ScriptModeSession can only be created once.")
        ScriptModeSession.instance = self

        ThreadBasedSession._active_session_cnt += 1

        self._on_task_command = on_task_command or (lambda _: None)
        self._on_session_close = lambda: None
        self._loop = loop

        # 会话结束时运行的函数
        self.deferred_functions = []

        self.threads = []  # 当前会话的线程
        self.unhandled_task_msgs = LimitedSizeQueue(maxsize=self.unhandled_task_mq_maxsize)

        self.task_mqs = {}  # task_id -> event msg queue
        self._closed = False

        # 用于实现回调函数的注册
        self.callback_mq = None
        self.callback_thread = None
        self.callbacks = {}  # callback_id -> (callback_func, is_mutex)

        tid = id(thread)
        event_mq = queue.Queue(maxsize=self.event_mq_maxsize)
        self.task_mqs[tid] = event_mq
