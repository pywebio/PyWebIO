r"""
.. autofunction:: run_async
.. autofunction:: run_asyncio_coroutine
.. autofunction:: register_thread
.. autoclass:: pywebio.session.coroutinebased.TaskHandle
   :members:
"""

import asyncio
import inspect
import threading
from functools import wraps

from .base import AbstractSession
from .coroutinebased import CoroutineBasedSession
from .threadbased import ThreadBasedSession, ScriptModeSession
from ..exceptions import SessionNotFoundException

_session_type = None

__all__ = ['run_async', 'run_asyncio_coroutine', 'register_thread']


def set_session_implement_for_target(target_func):
    """根据target_func函数类型设置会话实现"""
    global _session_type
    if asyncio.iscoroutinefunction(target_func) or inspect.isgeneratorfunction(target_func):
        _session_type = CoroutineBasedSession
    else:
        _session_type = ThreadBasedSession


def get_session_implement():
    global _session_type
    if _session_type is None:
        _session_type = ScriptModeSession
        _start_script_mode_server()
    return _session_type


def _start_script_mode_server():
    from ..platform.tornado import start_server_in_current_thread_session
    start_server_in_current_thread_session()


def get_current_session() -> "AbstractSession":
    return get_session_implement().get_current_session()


def get_current_task_id():
    return get_session_implement().get_current_task_id()


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
    """异步运行协程对象。协程中依然可以调用 PyWebIO 交互函数。 仅能在基于协程的会话上下文中调用

    :param coro_obj: 协程对象
    :return: An instance of  `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` is returned, which can be used later to close the task.
    """
    return get_current_session().run_async(coro_obj)


@check_session_impl(CoroutineBasedSession)
async def run_asyncio_coroutine(coro_obj):
    """若会话线程和运行事件的线程不是同一个线程，需要用 run_asyncio_coroutine 来运行asyncio中的协程。 仅能在基于协程的会话上下文中调用

    :param coro_obj: 协程对象
    """
    return await get_current_session().run_asyncio_coroutine(coro_obj)


@check_session_impl(ThreadBasedSession)
def register_thread(thread: threading.Thread):
    """注册线程，以便在线程内调用 PyWebIO 交互函数。仅能在基于线程的会话上下文中调用

    :param threading.Thread thread: 线程对象
    """
    return get_current_session().register_thread(thread)
