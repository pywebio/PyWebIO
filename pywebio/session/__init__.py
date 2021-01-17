r"""

.. autofunction:: run_async
.. autofunction:: run_asyncio_coroutine
.. autofunction:: download
.. autofunction:: run_js
.. autofunction:: eval_js
.. autofunction:: register_thread
.. autofunction:: defer_call
.. autofunction:: hold
.. autofunction:: data
.. autofunction:: set_env
.. autofunction:: go_app
.. autofunction:: get_info

.. autoclass:: pywebio.session.coroutinebased.TaskHandle
   :members:
"""

import threading
from base64 import b64encode
from functools import wraps

from .base import Session
from .coroutinebased import CoroutineBasedSession
from .threadbased import ThreadBasedSession, ScriptModeSession
from ..exceptions import SessionNotFoundException, SessionException
from ..utils import iscoroutinefunction, isgeneratorfunction, run_as_function, to_coroutine

# 当前进程中正在使用的会话实现的列表
_active_session_cls = []

__all__ = ['run_async', 'run_asyncio_coroutine', 'register_thread', 'hold', 'defer_call', 'data', 'get_info',
           'run_js', 'eval_js', 'download', 'set_env', 'go_app']


def register_session_implement_for_target(target_func):
    """根据target_func函数类型注册会话实现，并返回会话实现"""
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


def get_current_session() -> "Session":
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
    """
    装饰器，使用chose_impl对gen_func进行装饰后，gen_func() 操作将根据当前会话实现 返回协程对象 或 直接运行函数体
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
    """保持会话，直到用户关闭浏览器

    注意⚠️：在 :ref:`基于协程 <coroutine_based_session>` 的会话上下文中，需要使用 ``await hold()`` 语法来进行调用。
    """
    while True:
        try:
            yield next_client_event()
        except SessionException:
            return


def download(name, content):
    """向用户推送文件，用户浏览器会将文件下载到本地

    :param str name: 下载保存为的文件名
    :param content: 文件内容. 类型为 bytes-like object
    """
    from ..io_ctrl import send_msg
    content = b64encode(content).decode('ascii')
    send_msg('download', spec=dict(name=name, content=content))


def run_js(code_, **args):
    """运行js代码.

    代码运行在浏览器的JS全局作用域中

    :param str code_: js代码
    :param args: 传递给js代码的局部变量。变量值需要可以被json序列化

    Example::

        run_js('console.log(a + b)', a=1, b=2)

    """
    from ..io_ctrl import send_msg
    send_msg('run_script', spec=dict(code=code_, args=args))


@chose_impl
def eval_js(expression_, **args):
    """执行js表达式，并获取表达式的值

    :param str expression_: js表达式. 表达式的值需要能JSON序列化
    :return: js表达式的值
    :param args: 传递给js代码的局部变量。变量值需要可以被json序列化

    注意⚠️：在 :ref:`基于协程 <coroutine_based_session>` 的会话上下文中，需要使用 ``await eval_js(expression)`` 语法来进行调用。

    Example::

        current_url = eval_js("window.location.href")

        function_res = eval_js('''(function(){
            var a = 1;
            a += b;
            return a;
        })()''', b=100)
    """
    script = r"""
    (function(WebIO){
        let ____result____ = null;  // to avoid naming conflict
        try{
            ____result____ = eval(%r);
        }catch{};
        
        WebIO.sendMessage({
            event: "js_yield",
            task_id: WebIOCurrentTaskID,  // local var in run_script command
            data: ____result____ || null
        });
    })(WebIO);""" % expression_

    run_js(script, **args)

    res = yield next_client_event()
    assert res['event'] == 'js_yield', "Internal Error, please report this bug on " \
                                       "https://github.com/wang0618/PyWebIO/issues"
    return res['data']


@check_session_impl(CoroutineBasedSession)
def run_async(coro_obj):
    """异步运行协程对象。协程中依然可以调用 PyWebIO 交互函数。 仅能在 :ref:`基于协程 <coroutine_based_session>` 的会话上下文中调用

    :param coro_obj: 协程对象
    :return: `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` 实例。 通过 TaskHandle 可以查询协程运行状态和关闭协程。
    """
    return get_current_session().run_async(coro_obj)


@check_session_impl(CoroutineBasedSession)
async def run_asyncio_coroutine(coro_obj):
    """若会话线程和运行asyncio事件循环的线程不是同一个线程，需要用 `run_asyncio_coroutine()` 来运行asyncio中的协程。
    仅能在 :ref:`基于协程 <coroutine_based_session>` 的会话上下文中调用。

    :param coro_obj: `asyncio` 库中的协程对象

    在Flask和Django后端中，asyncio事件循环运行在一个单独的线程中，PyWebIO会话运行在其他线程，这时在基于协程的PyWebIO会话中 ``await`` 诸如
    `asyncio.sleep` 等 `asyncio` 库中的协程对象时，需配合 `run_asyncio_coroutine` 使用::

        async def app():
            put_text('hello')
            await run_asyncio_coroutine(asyncio.sleep(1))
            put_text('world')

        pywebio.platform.flask.start_server(app)

    """
    return await get_current_session().run_asyncio_coroutine(coro_obj)


@check_session_impl(ThreadBasedSession)
def register_thread(thread: threading.Thread):
    """注册线程，以便在线程内调用 PyWebIO 交互函数。仅能在默认的基于线程的会话上下文中调用。

    参见 :ref:`Server模式下并发与会话的结束 <thread_in_server_mode>`

    :param threading.Thread thread: 线程对象
    """
    return get_current_session().register_thread(thread)


def defer_call(func):
    """设置会话结束时调用的函数。无论是用户主动关闭会话还是任务结束会话关闭，设置的函数都会被运行。
    可以用于资源清理等工作。
    在会话中可以多次调用 `defer_call()` ,会话结束后将会顺序执行设置的函数。

    `defer_call` 同样支持以装饰器的方式使用::

         @defer_call
         def cleanup():
            pass

    :param func: 话结束时调用的函数

    .. attention:: 通过 `defer_call()` 设置的函数被调用时会话已经关闭，所以在函数体内不可以调用 PyWebIO 的交互函数

    """
    get_current_session().defer_call(func)
    return func


def data():
    """获取当前会话的数据对象，用于在对象上保存一些会话相关的数据。访问数据对象不存在的属性时会返回None而不是抛出异常。
    """
    return get_current_session().save


def set_env(**env_info):
    """当前会话的环境设置

    可配置项有:

    * ``title`` (str): 当前页面的标题
    * ``output_animation`` (bool): 是否启用输出动画（在输出内容时，使用过渡动画），默认启用
    * ``auto_scroll_bottom`` (bool): 是否在内容输出时将页面自动滚动到底部，默认关闭。注意，开启后，只有输出到ROOT Scope才可以触发自动滚动。
    * ``http_pull_interval`` (int): HTTP轮询后端消息的周期（单位为毫秒，默认1000ms），仅在基于HTTP连接的会话中可用（）

    调用示例::

        set_env(title='Awesome PyWebIO!!', output_animation=False)
    """
    from ..io_ctrl import send_msg
    assert all(k in ('title', 'output_animation', 'auto_scroll_bottom', 'http_pull_interval')
               for k in env_info.keys())
    send_msg('set_env', spec=env_info)


def go_app(name, new_window=True):
    """跳转PyWebIO任务，仅在PyWebIO Server模式下可用

    :param str name: PyWebIO任务名
    :param bool new_window: 是否在新窗口打开，默认为 `True`
    """
    run_js('javascript:WebIO.openApp(app, new_window)', app=name, new_window=new_window)


def get_info():
    """ 获取当前会话的相关信息

    :return: 表示会话信息的对象，属性有：

       * ``user_agent`` : 表示用户浏览器信息的对象，属性有

            * ``is_mobile`` (bool): 用户使用的设备是否为手机 (比如 iPhone, Android phones, Blackberry, Windows Phone 等设备)
            * ``is_tablet`` (bool): 用户使用的设备是否为平板 (比如 iPad, Kindle Fire, Nexus 7 等设备)
            * ``is_pc`` (bool): 用户使用的设备是否为桌面电脑 (比如运行 Windows, OS X, Linux 的设备)
            * ``is_touch_capable`` (bool): 用户使用的设备是否支持触控

            * ``browser.family`` (str): 浏览器家族. 比如 'Mobile Safari'
            * ``browser.version`` (tuple): 浏览器版本元组. 比如 (5, 1)
            * ``browser.version_string`` (str): 浏览器版本字符串. 比如 '5.1'

            * ``os.family`` (str): 操作系统家族. 比如 'iOS'
            * ``os.version`` (tuple): 操作系统版本元组. 比如 (5, 1)
            * ``os.version_string`` (str): 操作系统版本字符串. 比如 '5.1'

            * ``device.family`` (str): 设备家族. 比如 'iPhone'
            * ``device.brand`` (str): 设备品牌. 比如 'Apple'
            * ``device.model`` (str): 设备型号. 比如 'iPhone'

       * ``user_language`` (str): 用户操作系统使用的语言. 比如 ``'zh-CN'``
       * ``server_host`` (str): 当前会话的服务器host，包含域名和端口，端口为80时可以被省略
       * ``origin`` (str): 当前用户的页面地址. 包含 协议、主机、端口 部分. 比如 ``'http://localhost:8080'`` .
         可能为空，但保证当用户的页面地址不在当前服务器下(即 主机、端口部分和 ``server_host`` 不一致)时有值.
       * ``user_ip`` (str): 用户的ip地址.
       * ``backend`` (str): PyWebIO使用的Web框架名. 目前可用值有 ``'tornado'`` , ``'flask'`` , ``'django'`` , ``'aiohttp'`` .
       * ``request`` (object): 创建当前会话时的Web请求对象. 根据PyWebIO使用的后端Server不同，``request`` 的类型也不同:

            * 使用Tornado后端时, ``request`` 为
              `tornado.httputil.HTTPServerRequest <https://www.tornadoweb.org/en/stable/httputil.html#tornado.httputil.HTTPServerRequest>`_ 实例
            * 使用Flask后端时, ``request`` 为 `flask.Request <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>`_ 实例
            * 使用Django后端时, ``request`` 为 `django.http.HttpRequest <https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest>`_ 实例
            * 使用aiohttp后端时, ``request`` 为 `aiohttp.web.BaseRequest <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.BaseRequest>`_ 实例

    会话信息对象的 ``user_agent`` 属性是通过 user-agents 库进行解析生成的。参见 https://github.com/selwin/python-user-agents#usage
    """
    return get_current_session().info
