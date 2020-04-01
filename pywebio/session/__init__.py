r"""
.. autofunction:: run_async
.. autofunction:: run_asyncio_coroutine
.. autofunction:: register_thread
"""

import asyncio
import inspect
import threading
from functools import wraps

from .base import AbstractSession
from .coroutinebased import CoroutineBasedSession
from .threadbased import ThreadBasedSession, ScriptModeSession
from ..exceptions import SessionNotFoundException

THREAD_BASED = 'ThreadBased'
COROUTINE_BASED = 'CoroutineBased'
SCRIPT_MODE = 'ScriptMode'

_session_type = ThreadBasedSession

__all__ = ['run_async', 'run_asyncio_coroutine', 'register_thread', 'THREAD_BASED', 'COROUTINE_BASED']


def get_session_implement_for_target(target_func):
    """根据target_func函数类型获取默认会话实现"""
    if asyncio.iscoroutinefunction(target_func) or inspect.isgeneratorfunction(target_func):
        return COROUTINE_BASED
    return THREAD_BASED


def set_session_implement(session_type_name):
    """设置会话实现类. 仅用于PyWebIO内部使用"""
    global _session_type
    sessions = {THREAD_BASED: ThreadBasedSession, COROUTINE_BASED: CoroutineBasedSession, SCRIPT_MODE: ScriptModeSession}
    assert session_type_name in sessions, ValueError('No "%s" Session type ' % session_type_name)
    _session_type = sessions[session_type_name]


def get_session_implement():
    global _session_type
    return _session_type


def _start_script_mode_server():
    global _session_type
    from ..platform.tornado import start_server_in_current_thread_session
    _session_type = ScriptModeSession
    start_server_in_current_thread_session()


def get_current_session() -> "AbstractSession":
    try:
        return _session_type.get_current_session()
    except SessionNotFoundException:
        # 如果没已经运行的backend server，在当前线程上下文作为session启动backend server
        if get_session_implement().active_session_count() == 0:
            _start_script_mode_server()
            return _session_type.get_current_session()
        else:
            raise


def get_current_task_id():
    try:
        return _session_type.get_current_task_id()
    except RuntimeError:
        # 如果没已经运行的backend server，在当前线程上下文作为session启动backend server
        if get_session_implement().active_session_count() == 0:
            _start_script_mode_server()
            return _session_type.get_current_session()
        else:
            raise


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
    """异步运行协程对象。协程中依然可以调用 PyWebIO 交互函数。 仅能在 CoroutineBasedSession 会话上下文中调用

    :param coro_obj: 协程对象
    :return: An instance of  `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` is returned, which can be used later to close the task.
    """
    return get_current_session().run_async(coro_obj)


@check_session_impl(CoroutineBasedSession)
async def run_asyncio_coroutine(coro_obj):
    """若会话线程和运行事件的线程不是同一个线程，需要用 run_asyncio_coroutine 来运行asyncio中的协程

    :param coro_obj: 协程对象
    """
    return await get_current_session().run_asyncio_coroutine(coro_obj)


@check_session_impl(ThreadBasedSession)
def register_thread(thread: threading.Thread):
    """注册线程，以便在线程内调用 PyWebIO 交互函数。仅能在 ThreadBasedSession 会话上下文中调用

    :param threading.Thread thread: 线程对象
    """
    return get_current_session().register_thread(thread)
