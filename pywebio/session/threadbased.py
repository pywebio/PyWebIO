import asyncio
import inspect
import logging
import queue
import sys
import threading
import traceback

from .base import AbstractSession
from ..exceptions import SessionNotFoundException
from ..utils import random_str

logger = logging.getLogger(__name__)

"""
基于线程的会话实现

主任务线程退出后，连接关闭，但不会清理主任务线程产生的其他线程

客户端连接关闭后，后端线程不会退出，但是再次调用
todo: thread 重名
"""


# todo 线程安全
class ThreadBasedWebIOSession(AbstractSession):
    thread2session = {}  # thread_id -> session

    event_mq_maxsize = 100
    callback_mq_maxsize = 100

    @classmethod
    def get_current_session(cls) -> "ThreadBasedWebIOSession":
        curr = threading.current_thread().getName()
        session = cls.thread2session.get(curr)
        if session is None:
            raise SessionNotFoundException("Can't find current session. Maybe session closed.")
        return session

    @staticmethod
    def get_current_task_id():
        return threading.current_thread().getName()

    def __init__(self, target, on_task_message=None, on_session_close=None, loop=None):
        """
        :param target_func: 会话运行的函数
        :param on_coro_msg: 由协程内发给session的消息的处理函数
        :param on_session_close: 会话结束的处理函数。后端Backend在相应on_session_close时关闭连接时，
            需要保证会话内的所有消息都传送到了客户端
        :param loop: 事件循环。若on_task_message或者on_session_close中有调用使用asyncio事件循环的调用，
            则需要事件循环实例来将回调在事件循环的线程中执行
        """
        self._on_task_message = on_task_message or (lambda _: None)
        self._on_session_close = on_session_close or (lambda: None)
        self._loop = loop

        self._server_msg_lock = threading.Lock()
        self.threads = []  # 当前会话的线程id集合，用户会话结束后，清理数据
        self.unhandled_task_msgs = []

        self.event_mqs = {}  # thread_id -> event msg queue
        self._closed = False

        # 用于实现回调函数的注册
        self.callback_mq = None
        self.callback_thread = None
        self.callbacks = {}  # callback_id -> (callback_func, is_mutex)

        self._start_main_task(target)

    def _start_main_task(self, target):
        assert (not asyncio.iscoroutinefunction(target)) and (not inspect.isgeneratorfunction(target)), ValueError(
            "In ThreadBasedWebIOSession.__init__, `target` must be a simple function, "
            "not coroutine function or generator function. ")

        def thread_task(target):
            try:
                target()
            except Exception as e:
                self.on_task_exception()
            finally:
                self.send_task_message(dict(command='close_session'))
                self.close()

        task_name = '%s-%s' % (target.__name__, random_str(10))
        thread = threading.Thread(target=thread_task, kwargs=dict(target=target),
                                  daemon=True, name=task_name)
        self.register_thread(thread)

        thread.start()

    def send_task_message(self, message):
        """向会话发送来自协程内的消息

        :param dict message: 消息
        """
        with self._server_msg_lock:
            self.unhandled_task_msgs.append(message)
        if self._loop:
            self._loop.call_soon_threadsafe(self._on_task_message, self)
        else:
            self._on_task_message(self)

    def next_client_event(self):
        name = threading.current_thread().getName()
        event_mq = self.get_current_session().event_mqs.get(name)
        return event_mq.get()

    def send_client_event(self, event):
        """向会话发送来自用户浏览器的事件️

        :param dict event: 事件️消息
        """
        task_id = event['coro_id']
        mq = self.event_mqs.get(task_id)
        if not mq and task_id in self.callbacks:
            mq = self.callback_mq

        if not mq:
            logger.error('event_mqs not found, task_id:%s', task_id)
            return

        mq.put(event)

    def get_task_messages(self):
        with self._server_msg_lock:
            msgs = self.unhandled_task_msgs
            self.unhandled_task_msgs = []
        return msgs

    def _cleanup(self):
        self.event_mqs = {}
        # Don't clean unhandled_task_msgs, it may not send to client
        # self.unhandled_task_msgs = []
        for t in self.threads:
            del ThreadBasedWebIOSession.thread2session[t]
            # pass

        if self.callback_mq is not None:  # 回调功能已经激活
            self.callback_mq.put(None)  # 结束回调线程

    def close(self, no_session_close_callback=False):
        """关闭当前Session

        :param bool no_session_close_callback: 不调用 on_session_close 会话结束的处理函数。
            当 close 是由后端Backend调用时可能希望开启 no_session_close_callback
        """
        self._cleanup()
        self._closed = True
        if not no_session_close_callback:
            if self._loop:
                self._loop.call_soon_threadsafe(self._on_session_close)
            else:
                self._on_session_close()

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

    def _activate_callback_env(self):
        """激活回调功能

        ThreadBasedWebIOSession的回调实现原理是：创建一个单独的线程用于接收回调事件，进而调用相关的回调函数。
        当用户Task中并没有使用到回调功能时，不必开启此线程，可以节省资源
        """

        if self.callback_mq is not None:  # 回调功能已经激活
            return

        self.callback_mq = queue.Queue(maxsize=self.callback_mq_maxsize)
        self.callback_thread = threading.Thread(target=self._dispatch_callback_event,
                                                daemon=True, name='callback-' + random_str(10))
        self.register_thread(self.callback_thread)
        self.callback_thread.start()
        logger.debug('Callback thread start')

    def _dispatch_callback_event(self):
        while not self.closed():
            event = self.callback_mq.get()
            if event is None:  # 结束信号
                break
            callback_info = self.callbacks.get(event['coro_id'])
            if not callback_info:
                logger.error("No callback for coro_id:%s", event['coro_id'])
                return
            callback, mutex = callback_info

            def run(callback):
                try:
                    callback(event['data'])
                except:
                    ThreadBasedWebIOSession.get_current_session().on_task_exception()

            if mutex:
                run(callback)
            else:
                t = threading.Thread(target=run, kwargs=dict(callback=callback),
                                     daemon=True, name=event['coro_id'])
                self.register_thread(t)
                t.start()

    def register_callback(self, callback, serial_mode=False):
        """ 向Session注册一个回调函数，返回回调id

        Session需要保证当收到前端发送的事件消息 ``{event: "callback"，coro_id: 回调id, data:...}`` 时，
        ``callback`` 回调函数被执行， 并传入事件消息中的 ``data`` 字段值作为参数

        :param bool serial_mode: 串行模式模式。若为 ``True`` ，则对于同一组件的点击事件，串行执行其回调函数
        """
        assert (not asyncio.iscoroutinefunction(callback)) and (not inspect.isgeneratorfunction(callback)), ValueError(
            "In ThreadBasedWebIOSession.register_callback, `callback` must be a simple function, "
            "not coroutine function or generator function. ")

        self._activate_callback_env()
        callback_id = 'CB-%s-%s' % (getattr(callback, '__name__', ''), random_str(10))
        self.callbacks[callback_id] = (callback, serial_mode)
        return callback_id

    def register_thread(self, t: threading.Thread, as_daemon=True):
        """注册线程，以便在线程内调用 pywebio 交互函数

        :param threading.Thread thread: 线程对象
        :param bool as_daemon: 是否将线程设置为 daemon 线程. 默认为 True
        """
        if as_daemon:
            t.setDaemon(True)
        tname = t.getName()
        self.threads.append(tname)
        self.thread2session[tname] = self
        event_mq = queue.Queue(maxsize=self.event_mq_maxsize)
        self.event_mqs[tname] = event_mq


class DesignatedThreadSession(ThreadBasedWebIOSession):
    """以指定进程为会话"""

    def __init__(self, thread, on_task_message=None, loop=None):
        """
        :param on_coro_msg: 由协程内发给session的消息的处理函数
        :param on_session_close: 会话结束的处理函数。后端Backend在相应on_session_close时关闭连接时，
            需要保证会话内的所有消息都传送到了客户端
        :param loop: 事件循环。若on_task_message或者on_session_close中有调用使用asyncio事件循环的调用，
            则需要事件循环实例来将回调在事件循环的线程中执行

        """
        self._on_task_message = on_task_message or (lambda _: None)
        self._on_session_close = lambda: None
        self._loop = loop

        self._server_msg_lock = threading.Lock()
        self.threads = []  # 当前会话的线程id集合，用户会话结束后，清理数据
        self.unhandled_task_msgs = []

        self.event_mqs = {}  # thread_id -> event msg queue
        self._closed = False

        # 用于实现回调函数的注册
        self.callback_mq = None
        self.callback_thread = None
        self.callbacks = {}  # callback_id -> (callback_func, is_mutex)

        self.register_thread(thread, as_daemon=False)
