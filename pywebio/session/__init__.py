import threading
from functools import wraps

from .asyncbased import AsyncBasedSession
from .base import AbstractSession
from .threadbased import ThreadBasedWebIOSession, DesignatedThreadSession
from ..exceptions import SessionNotFoundException

_session_type = ThreadBasedWebIOSession

__all__ = ['set_session_implement', 'run_async', 'asyncio_coroutine', 'register_thread']

_server_started = False


def mark_server_started():
    """标记服务端已经启动"""
    global _server_started
    _server_started = True


def set_session_implement(session_type):
    global _session_type
    assert session_type in [ThreadBasedWebIOSession, AsyncBasedSession, DesignatedThreadSession]
    _session_type = session_type


def get_session_implement():
    global _session_type
    return _session_type


def _start_script_mode_server():
    from ..platform import start_server_in_current_thread_session
    set_session_implement(DesignatedThreadSession)
    start_server_in_current_thread_session()


def get_current_session() -> "AbstractSession":
    try:
        return _session_type.get_current_session()
    except SessionNotFoundException:
        if _server_started:
            raise
        # 没有显式启动backend server时，在当前线程上下文作为session启动backend server
        _start_script_mode_server()
        return _session_type.get_current_session()


def get_current_task_id():
    try:
        return _session_type.get_current_task_id()
    except RuntimeError:
        if _server_started:
            raise
        # 没有显式启动backend server时，在当前线程上下文作为session启动backend server
        _start_script_mode_server()
        return _session_type.get_current_task_id()


def check_session_impl(session_type):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            now_impl = get_session_implement()
            if not issubclass(now_impl,
                              session_type):  # Check if 'now_impl' is a derived from session_type or is the same class
                func_name = getattr(func, '__name__', str(func))
                require = getattr(session_type, '__name__', str(session_type))
                now = getattr(now_impl, '__name__', str(now_impl))

                raise RuntimeError("Only can invoke `{func_name:s}` in {require:s} context."
                                   " You are now in {now:s} context".format(func_name=func_name, require=require,
                                                                            now=now))
            return func(*args, **kwargs)

        return inner

    return decorator


@check_session_impl(AsyncBasedSession)
def run_async(coro_obj):
    """异步运行协程对象，协程中依然可以调用 PyWebIO 交互函数。 仅能在 AsyncBasedSession 会话上下文中调用

    :param coro_obj: 协程对象
    """
    AsyncBasedSession.get_current_session().run_async(coro_obj)


@check_session_impl(AsyncBasedSession)
async def asyncio_coroutine(coro):
    """若会话线程和运行事件的线程不是同一个线程，需要用 asyncio_coroutine 来运行asyncio中的协程

    :param coro_obj: 协程对象
    """
    return await AsyncBasedSession.get_current_session().asyncio_coroutine(coro)


@check_session_impl(ThreadBasedWebIOSession)
def register_thread(thread: threading.Thread, as_daemon=True):
    """注册线程，以便在线程内调用 PyWebIO 交互函数。仅能在 ThreadBasedWebIOSession 会话上下文中调用

    :param threading.Thread thread: 线程对象
    :param bool as_daemon: 是否将线程设置为 daemon 线程. 默认为 True
    """
    return ThreadBasedWebIOSession.get_current_session().register_thread(thread, as_daemon=as_daemon)
