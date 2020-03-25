import threading
from functools import wraps

from .coroutinebased import CoroutineBasedSession
from .base import AbstractSession
from .threadbased import ThreadBasedSession, DesignatedThreadSession
from ..exceptions import SessionNotFoundException

_session_type = ThreadBasedSession

__all__ = ['run_async', 'run_asyncio_coroutine', 'register_thread']

_server_started = False


def mark_server_started():
    """标记服务端已经启动. 仅用于PyWebIO内部使用"""
    global _server_started
    _server_started = True


def set_session_implement(session_type):
    """设置会话实现类. 仅用于PyWebIO内部使用"""
    global _session_type
    assert session_type in [ThreadBasedSession, CoroutineBasedSession, DesignatedThreadSession]
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


@check_session_impl(CoroutineBasedSession)
def run_async(coro_obj):
    """异步运行协程对象，协程中依然可以调用 PyWebIO 交互函数。 仅能在 CoroutineBasedSession 会话上下文中调用

    :param coro_obj: 协程对象
    """
    get_current_session().run_async(coro_obj)


@check_session_impl(CoroutineBasedSession)
async def run_asyncio_coroutine(coro_obj):
    """若会话线程和运行事件的线程不是同一个线程，需要用 run_asyncio_coroutine 来运行asyncio中的协程

    :param coro_obj: 协程对象
    """
    return await get_current_session().run_asyncio_coroutine(coro_obj)


@check_session_impl(ThreadBasedSession)
def register_thread(thread: threading.Thread, as_daemon=True):
    """注册线程，以便在线程内调用 PyWebIO 交互函数。仅能在 ThreadBasedSession 会话上下文中调用

    :param threading.Thread thread: 线程对象
    """
    return get_current_session().register_thread(thread, as_daemon=as_daemon)
