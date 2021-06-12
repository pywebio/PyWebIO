r"""

.. autofunction:: run_async
.. autofunction:: run_asyncio_coroutine
.. autofunction:: download
.. autofunction:: run_js
.. autofunction:: eval_js
.. autofunction:: register_thread
.. autofunction:: defer_call
.. autofunction:: hold

.. data:: local

    The session-local object for current session.

    ``local`` is a dictionary that can be accessed through attributes. When accessing a property that does not exist in the data object, it returns ``None`` instead of throwing an exception.
    The method of dictionary is not supported in ``local``. It supports the ``in`` operator to determine whether the key exists. You can use ``local._dict`` to get the underlying dictionary data.


    :Usage Scenes:

    When you need to share some session-independent data with multiple functions, it is more convenient to use session-local objects to save state than to use function parameters.

    Here is a example of a session independent counter implementation::

        from pywebio.session import local
        def add():
            local.cnt = (local.cnt or 0) + 1

        def show():
            put_text(local.cnt or 0)

        def main():
            put_buttons(['Add counter', 'Show counter'], [add, show])
            hold()

    The way to pass state through function parameters is::

        from functools import partial
        def add(cnt):
            cnt[0] += 1

        def show(cnt):
            put_text(cnt[0])

        def main():
            cnt = [0]  # Trick: to pass by reference
            put_buttons(['Add counter', 'Show counter'], [partial(add, cnt), partial(show, cnt)])
            hold()

    Of course, you can also use function closures to achieved the same::

        def main():
            cnt = 0

            def add():
                nonlocal cnt
                cnt += 1

            def show():
                put_text(cnt)

            put_buttons(['Add counter', 'Show counter'], [add, show])
            hold()

    :``local`` usage:

    ::

        local.name = "Wang"
        local.age = 22
        assert local.foo is None
        local[10] = "10"

        for key in local:
            print(key)

        assert 'bar' not in local
        assert 'name' in local

        print(local._dict)

    .. versionadded:: 1.1

.. autofunction:: set_env
.. autofunction:: go_app

.. data:: info

    The session information data object, whose attributes are:

       * ``user_agent`` : The Object of the user browser information, whose attributes are

            * ``is_mobile`` (bool): whether user agent is identified as a mobile phone (iPhone, Android phones, Blackberry, Windows Phone devices etc)
            * ``is_tablet`` (bool): whether user agent is identified as a tablet device (iPad, Kindle Fire, Nexus 7 etc)
            * ``is_pc`` (bool): whether user agent is identified to be running a traditional "desktop" OS (Windows, OS X, Linux)
            * ``is_touch_capable`` (bool): whether user agent has touch capabilities

            * ``browser.family`` (str): Browser family. such as 'Mobile Safari'
            * ``browser.version`` (tuple): Browser version. such as (5, 1)
            * ``browser.version_string`` (str): Browser version string. such as '5.1'

            * ``os.family`` (str): User OS family. such as 'iOS'
            * ``os.version`` (tuple): User OS version. such as (5, 1)
            * ``os.version_string`` (str): User OS version string. such as '5.1'

            * ``device.family`` (str): User agent's device family. such as 'iPhone'
            * ``device.brand`` (str): Device brand. such as 'Apple'
            * ``device.model`` (str): Device model. such as 'iPhone'

       * ``user_language`` (str): Language used by the user's operating system. (e.g., ``'zh-CN'``)
       * ``server_host`` (str): PyWebIO server host, including domain and port, the port can be omitted when 80.
       * ``origin`` (str): Indicate where the user from. Including protocol, host, and port parts. Such as ``'http://localhost:8080'`` .
         It may be empty, but it is guaranteed to have a value when the user's page address is not under the server host. (that is, the host, port part are inconsistent with ``server_host``).
       * ``user_ip`` (str): User's ip address.
       * ``backend`` (str): The current PyWebIO backend server implementation. The possible values are ``'tornado'``, ``'flask'``, ``'django'`` , ``'aiohttp'`` , ``'starlette'``.
       * ``protocol`` (str): The communication protocol between PyWebIO server and browser. The possible values are ``'websocket'``, ``'http'``
       * ``request`` (object): The request object when creating the current session. Depending on the backend server, the type of ``request`` can be:

            * When using Tornado, ``request`` is instance of
              `tornado.httputil.HTTPServerRequest <https://www.tornadoweb.org/en/stable/httputil.html#tornado.httputil.HTTPServerRequest>`_
            * When using Flask, ``request`` is instance of `flask.Request <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>`_
            * When using Django, ``request`` is instance of `django.http.HttpRequest <https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest>`_
            * When using aiohttp, ``request`` is instance of `aiohttp.web.BaseRequest <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.BaseRequest>`_
            * When using FastAPI/Starlette, ``request`` is instance of `starlette.websockets.WebSocket <https://www.starlette.io/websockets/>`_

    The ``user_agent`` attribute of the session information object is parsed by the user-agents library. See https://github.com/selwin/python-user-agents#usage

    .. versionchanged:: 1.2

       Added the ``protocol`` attribute.

    Example:

    .. exportable-codeblock::
        :name: get_info
        :summary: `session.info` usage

        import json
        from pywebio.session import info as session_info

        put_code(json.dumps({
            k: str(getattr(session_info, k))
            for k in ['user_agent', 'user_language', 'server_host',
                      'origin', 'user_ip', 'backend', 'protocol', 'request']
        }, indent=4), 'json')

.. autoclass:: pywebio.session.coroutinebased.TaskHandler
   :members:
"""

import threading
from base64 import b64encode
from functools import wraps

import user_agents

from .base import Session
from .coroutinebased import CoroutineBasedSession
from .threadbased import ThreadBasedSession, ScriptModeSession
from ..exceptions import SessionNotFoundException, SessionException
from ..utils import iscoroutinefunction, isgeneratorfunction, run_as_function, to_coroutine, ObjectDictProxy, \
    ReadOnlyObjectDict

# 当前进程中正在使用的会话实现的列表
# List of session implementations currently in use
_active_session_cls = []

__all__ = ['run_async', 'run_asyncio_coroutine', 'register_thread', 'hold', 'defer_call', 'data', 'get_info',
           'run_js', 'eval_js', 'download', 'set_env', 'go_app', 'local', 'info']


def register_session_implement(cls):
    if cls not in _active_session_cls:
        _active_session_cls.append(cls)

    return cls


def register_session_implement_for_target(target_func):
    """根据target_func函数类型注册会话实现，并返回会话实现
    Register the session implementation according to the target_func function type, and return the session implementation"""
    if iscoroutinefunction(target_func) or isgeneratorfunction(target_func):
        cls = CoroutineBasedSession
    else:
        cls = ThreadBasedSession

    if ScriptModeSession in _active_session_cls:
        raise RuntimeError("Already in script mode, can't start server")

    if cls not in _active_session_cls:
        _active_session_cls.append(cls)

    return cls


def get_session_implement():
    """获取当前会话实现。仅供内部实现使用。应在会话上下文中调用
    Get the current session implementation. For internal implementation use only. Should be called in session context"""
    if not _active_session_cls:
        _active_session_cls.append(ScriptModeSession)
        _start_script_mode_server()

    # 当前正在使用的会话实现只有一个
    # There is only one session implementation currently in use
    if len(_active_session_cls) == 1:
        return _active_session_cls[0]

    # 当前有多个正在使用的会话实现
    # There are currently multiple session implementations in use
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


def get_current_session() -> "Session":
    return get_session_implement().get_current_session()


def get_current_task_id():
    return get_session_implement().get_current_task_id()


def check_session_impl(session_type):
    def decorator(func):
        """装饰器：在函数调用前检查当前会话实现是否满足要求
        Decorator: Check whether the current session implementation meets the requirements before the function call"""

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
    """
    装饰器，使用chose_impl对gen_func进行装饰后，gen_func() 调用将根据当前会话实现来确定是 返回协程对象 还是 直接运行函数体

    Decorator, after using `choose_impl` to decorate `gen_func`, according to the current session implementation, the `gen_func()` call will either return the coroutine object or directly run the function body
    """

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
    """Keep the session alive until the browser page is closed by user.

    .. note::

        After the PyWebIO session closed, the functions that need communicate with the PyWebIO server (such as the event callback of `put_buttons()` and download link of `put_file()`) will not work. You can call the ``hold()`` function at the end of the task function to hold the session, so that the event callback and download link will always be available before the browser page is closed by user.

    Note: When using :ref:`coroutine-based session <coroutine_based_session>`, you need to use the ``await hold()`` syntax to call the function.
    """
    while True:
        try:
            yield next_client_event()
        except SessionException:
            return


def download(name, content):
    """Send file to user, and the user browser will download the file to the local

    :param str name: File name when downloading
    :param content: File content. It is a bytes-like object

    Example:

    .. exportable-codeblock::
        :name: download
        :summary: `download()` usage

        put_buttons(['Click to download'],
                    [lambda: download('hello-world.txt', b'hello world!')])

    """
    from ..io_ctrl import send_msg
    content = b64encode(content).decode('ascii')
    send_msg('download', spec=dict(name=name, content=content))


def run_js(code_, **args):
    """Execute JavaScript code in user browser.

    The code is run in the browser's JS global scope.

    :param str code_: JavaScript code
    :param args: Local variables passed to js code. Variables need to be JSON-serializable.

    Example::

        run_js('console.log(a + b)', a=1, b=2)

    """
    from ..io_ctrl import send_msg
    send_msg('run_script', spec=dict(code=code_, args=args))


@chose_impl
def eval_js(expression_, **args):
    """Execute JavaScript expression in the user's browser and get the value of the expression

    :param str expression_: JavaScript expression. The value of the expression need to be JSON-serializable.
       If the value of the expression is a `promise <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise>`_,
       ``eval_js()`` will wait for the promise to resolve and return the value of it. When the promise is rejected, `None` is returned.
    :param args: Local variables passed to js code. Variables need to be JSON-serializable.
    :return: The value of the expression.

    Note: When using :ref:`coroutine-based session <coroutine_based_session>`, you need to use the ``await eval_js(expression)`` syntax to call the function.

    Example:

    .. exportable-codeblock::
        :name: eval_js
        :summary: `eval_js()` usage

        current_url = eval_js("window.location.href")
        put_text(current_url)  # ..demo-only

        ## ----
        function_res = eval_js('''(function(){
            var a = 1;
            a += b;
            return a;
        })()''', b=100)
        put_text(function_res)  # ..demo-only

        ## ----
        promise_res = eval_js('''new Promise(resolve => {
            setTimeout(() => {
                resolve('Returned inside callback.');
            }, 2000);
        });''')
        put_text(promise_res)  # ..demo-only

    .. versionchanged:: 1.3

       The JS expression support return promise.
    """

    from ..io_ctrl import send_msg
    send_msg('run_script', spec=dict(code=expression_, args=args, eval=True))

    res = yield next_client_event()
    assert res['event'] == 'js_yield', "Internal Error, please report this bug on " \
                                       "https://github.com/wang0618/PyWebIO/issues"
    return res['data']


@check_session_impl(CoroutineBasedSession)
def run_async(coro_obj):
    """Run the coroutine object asynchronously. PyWebIO interactive functions are also available in the coroutine.

    ``run_async()`` can only be used in :ref:`coroutine-based session <coroutine_based_session>`.

    :param coro_obj: Coroutine object
    :return: `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` instance, which can be used to query the running status of the coroutine or close the coroutine.

    See also: :ref:`Concurrency in coroutine-based sessions <coroutine_based_concurrency>`
    """
    return get_current_session().run_async(coro_obj)


@check_session_impl(CoroutineBasedSession)
async def run_asyncio_coroutine(coro_obj):
    """
    If the thread running sessions are not the same as the thread running the asyncio event loop, you need to wrap ``run_asyncio_coroutine()`` to run the coroutine in asyncio.

    Can only be used in :ref:`coroutine-based session <coroutine_based_session>`.

    :param coro_obj: Coroutine object in `asyncio`

    Example::

        async def app():
            put_text('hello')
            await run_asyncio_coroutine(asyncio.sleep(1))
            put_text('world')

        pywebio.platform.flask.start_server(app)

    """
    return await get_current_session().run_asyncio_coroutine(coro_obj)


@check_session_impl(ThreadBasedSession)
def register_thread(thread: threading.Thread):
    """Register the thread so that PyWebIO interactive functions are available in the thread.

    Can only be used in the thread-based session.

    See :ref:`Concurrent in Server mode <thread_in_server_mode>`

    :param threading.Thread thread: Thread object
    """
    return get_current_session().register_thread(thread)


def defer_call(func):
    """Set the function to be called when the session closes.

    Whether it is because the user closes the page or the task finishes to cause session closed, the function set by ``defer_call(func)`` will be executed. Can be used for resource cleaning.

    You can call ``defer_call(func)`` multiple times in the session, and the set functions will be executed sequentially after the session closes.

    ``defer_call()`` can also be used as decorator::

         @defer_call
         def cleanup():
            pass

    .. attention:: PyWebIO interactive functions cannot be called inside the deferred functions.

    """
    get_current_session().defer_call(func)
    return func


# session-local data object
local = ObjectDictProxy(lambda: get_current_session().save)


def data():
    """Get the session-local object of current session.


    .. deprecated:: 1.1
        Use `local <pywebio.session.local>` instead.
    """
    global local

    import warnings
    warnings.warn("`pywebio.session.data()` is deprecated since v1.1 and will remove in the future version, "
                  "use `pywebio.session.local` instead", DeprecationWarning, stacklevel=2)
    return local


def set_env(**env_info):
    """Config the environment of current session.

    Available configuration are:

    * ``title`` (str): Title of current page.
    * ``output_animation`` (bool): Whether to enable output animation, enabled by default
    * ``auto_scroll_bottom`` (bool): Whether to automatically scroll the page to the bottom after output content, it is closed by default.  Note that after enabled, only outputting to ROOT scope can trigger automatic scrolling.
    * ``http_pull_interval`` (int): The period of HTTP polling messages (in milliseconds, default 1000ms), only available in sessions based on HTTP connection.
    * ``input_panel_fixed`` (bool): Whether to make input panel fixed at bottom, enabled by default
    * ``input_panel_min_height`` (int): The minimum height of input panel (in pixel, default 300px), it should be larger than 75px. Available only when ``input_panel_fixed=True``
    * ``input_panel_init_height`` (int): The initial height of input panel (in pixel, default 300px), it should be larger than 175px. Available only when ``input_panel_fixed=True``
    * ``input_auto_focus`` (bool): Whether to focus on input automatically after showing input panel, default is ``True``

    Example::

        set_env(title='Awesome PyWebIO!!', output_animation=False)
    """
    from ..io_ctrl import send_msg
    assert all(k in ('title', 'output_animation', 'auto_scroll_bottom', 'http_pull_interval',
                     'input_panel_min_height', 'input_panel_init_height', 'input_panel_fixed', 'input_auto_focus')
               for k in env_info.keys())
    send_msg('set_env', spec=env_info)


def go_app(name, new_window=True):
    """Jump to another task of a same PyWebIO application. Only available in PyWebIO Server mode

    :param str name: Target PyWebIO task name.
    :param bool new_window: Whether to open in a new window, the default is `True`

    See also: :ref:`Server mode <server_and_script_mode>`
    """
    run_js('javascript:WebIO.openApp(app, new_window)', app=name, new_window=new_window)


# session info data object
info = ReadOnlyObjectDict(lambda: get_current_session().internal_save['info'])  # type: _SessionInfoType


class _SessionInfoType:
    user_agent = None  # type: user_agents.parsers.UserAgent
    user_language = ''  # e.g.: zh-CN
    server_host = ''  # e.g.: localhost:8080
    origin = ''  # e.g.: http://localhost:8080
    user_ip = ''
    backend = ''  # one of ['tornado', 'flask', 'django', 'aiohttp']
    protocol = ''  # one of ['websocket', 'http']
    request = None


def get_info():
    """Get information about the current session

    .. deprecated:: 1.2
        Use `info <pywebio.session.info>` instead.
    """
    global info

    import warnings
    warnings.warn("`pywebio.session.get_info()` is deprecated since v1.2 and will remove in the future version, "
                  "please use `pywebio.session.info` instead", DeprecationWarning, stacklevel=2)
    return info
