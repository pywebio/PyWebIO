r"""
.. autofunction:: run_async
.. autofunction:: run_asyncio_coroutine
.. autofunction:: register_thread
.. autofunction:: defer_call
.. autofunction:: hold

.. autoclass:: pywebio.session.coroutinebased.TaskHandle
   :members:
"""

import threading
from functools import wraps

from .base import AbstractSession
from .coroutinebased import CoroutineBasedSession
from .threadbased import ThreadBasedSession, ScriptModeSession
from ..exceptions import SessionNotFoundException
from ..utils import iscoroutinefunction, isgeneratorfunction, run_as_function, to_coroutine

# 当前进程中正在使用的会话实现的列表
_active_session_cls = []

__all__ = ['run_async', 'run_asyncio_coroutine', 'register_thread', 'hold', 'defer_call']


def register_session_implement_for_target(target_func):
    """根据target_func函数类型注册会话实现，并返回会话实现"""
    if iscoroutinefunction(target_func) or isgeneratorfunction(target_func):
        cls = CoroutineBasedSession
    else:
        cls = ThreadBasedSession

    if cls not in _active_session_cls:
        _active_session_cls.append(cls)

    return cls


def get_session_implement():
    """获取当前会话实现。仅供内部实现使用。应在会话上下文中调用"""
    if not _active_session_cls:
        _active_session_cls.append(ScriptModeSession)
        _start_script_mode_server()

    # 当前正在使用的会话实现只有一个
    if len(_active_session_cls) == 1:
        return _active_session_cls[0]

    # 当前有多个正在使用的会话实现
    for cls in _active_session_cls:
        try:
            cls.get_current_session()
            return cls
        except SessionNotFoundException:
            pass

    raise SessionNotFoundException


def _start_script_mode_server():
    from ..platform.tornado import start_server_in_current_thread_session
    start_server_in_current_thread_session()


def get_current_session() -> "AbstractSession":
    return get_session_implement().get_current_session()


def get_current_task_id():
    return get_session_implement().get_current_task_id()


def check_session_impl(session_type):
    def decorator(func):
        """装饰器：在函数调用前检查当前会话实现是否满足要求"""

        @wraps(func)
        def inner(*args, **kwargs):
            curr_impl = get_session_implement()

            # Check if 'now_impl' is a derived from session_type or is the same class
            if not issubclass(curr_impl, session_type):
                func_name = getattr(func, '__name__', str(func))
                require = getattr(session_type, '__name__', str(session_type))
                curr = getattr(curr_impl, '__name__', str(curr_impl))

                raise RuntimeError("Only can invoke `{func_name:s}` in {require:s} context."
                                   " You are now in {curr:s} context".format(func_name=func_name, require=require,
                                                                             curr=curr))
            return func(*args, **kwargs)

        return inner

    return decorator


def chose_impl(gen_func):
    """根据当前会话实现来将 gen_func 转化为协程对象或直接以函数运行"""

    @wraps(gen_func)
    def inner(*args, **kwargs):
        gen = gen_func(*args, **kwargs)
        if get_session_implement() == CoroutineBasedSession:
            return to_coroutine(gen)
        else:
            return run_as_function(gen)

    return inner


@chose_impl
def next_client_event():
    res = yield get_current_session().next_client_event()
    return res


@chose_impl
def hold():
    """保持会话，直到用户关闭浏览器，
    此时函数抛出 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常。

    注意⚠️：在 :ref:`基于协程 <coroutine_based_session>` 的会话上下文中，需要使用 ``await hold()`` 语法来进行调用。
    """
    while True:
        yield next_client_event()


@check_session_impl(CoroutineBasedSession)
def run_async(coro_obj):
    """异步运行协程对象。协程中依然可以调用 PyWebIO 交互函数。 仅能在 :ref:`基于协程 <coroutine_based_session>` 的会话上下文中调用

    :param coro_obj: 协程对象
    :return: An instance of  `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` is returned, which can be used later to close the task.
    """
    return get_current_session().run_async(coro_obj)


@check_session_impl(CoroutineBasedSession)
async def run_asyncio_coroutine(coro_obj):
    """若会话线程和运行事件的线程不是同一个线程，需要用 run_asyncio_coroutine 来运行asyncio中的协程。 仅能在 :ref:`基于协程 <coroutine_based_session>` 的会话上下文中调用。

    :param coro_obj: 协程对象
    """
    return await get_current_session().run_asyncio_coroutine(coro_obj)


@check_session_impl(ThreadBasedSession)
def register_thread(thread: threading.Thread):
    """注册线程，以便在线程内调用 PyWebIO 交互函数。仅能在默认的基于线程的会话上下文中调用。

    :param threading.Thread thread: 线程对象
    """
    return get_current_session().register_thread(thread)


def defer_call(func):
    """设置会话结束时调用的函数。无论是用户主动关闭会话还是任务结束会话关闭，设置的函数都会被运行。
    可以用于资源清理等工作。
    在会话中可以多次调用 `defer_call()` ,会话结束后将会顺序执行设置的函数。

    :param func: 话结束时调用的函数
    """
    return get_current_session().defer_call(func)
