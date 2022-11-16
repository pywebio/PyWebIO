import logging
import sys
import traceback
from collections import defaultdict

import user_agents
from ..exceptions import SessionException

logger = logging.getLogger(__name__)


class Session:
    """
    会话对象，由Backend创建

    属性：
        info 表示会话信息的对象
        save 会话的数据对象，提供用户在对象上保存一些会话相关数据

    由Task在当前Session上下文中调用：
        get_current_session
        get_current_task_id

        get_scope_name
        pop_scope
        push_scope
        send_task_command
        next_client_event
        on_task_exception
        register_callback
        need_keep_alive

        defer_call

    由Backend调用：
        send_client_event
        get_task_commands
        close

    Task和Backend都可调用：
        closed

    Session是不同的后端Backend与协程交互的桥梁：
        后端Backend在接收到用户浏览器的数据后，会通过调用 ``send_client_event`` 来通知会话，进而由Session驱动协程的运行。
        Task内在调用输入输出函数后，会调用 ``send_task_command`` 向会话发送输入输出消息指令， Session将其保存并留给后端Backend处理。
    """
    debug = False

    @staticmethod
    def get_current_session() -> "Session":
        raise NotImplementedError

    @staticmethod
    def get_current_task_id():
        raise NotImplementedError

    def __init__(self, session_info):
        """
        :param session_info: 会话信息。可以通过 Session.info 访问
        """
        self.internal_save = dict(info=session_info)  # some session related info, just for internal used
        self.save = {}  # underlying implement of `pywebio.session.data`
        self.scope_stack = defaultdict(lambda: ['ROOT'])  # task_id -> scope栈

        self.deferred_functions = []  # 会话结束时运行的函数
        self._closed = False

    def get_scope_name(self, idx):
        """获取当前任务的scope栈检索scope名

        :param int idx: scope栈的索引
        :return: scope名，不存在时返回 None
        """
        task_id = type(self).get_current_task_id()
        try:
            return self.scope_stack[task_id][idx]
        except IndexError:
            raise ValueError("Scope not found")

    def pop_scope(self):
        """弹出当前scope

        :return: 当前scope名
        """
        task_id = type(self).get_current_task_id()
        try:
            return self.scope_stack[task_id].pop()
        except IndexError:
            raise ValueError("ROOT Scope can't pop") from None

    def push_scope(self, name):
        """进入新scope"""
        task_id = type(self).get_current_task_id()
        self.scope_stack[task_id].append(name)

    def send_task_command(self, command):
        raise NotImplementedError

    def next_client_event(self) -> dict:
        """获取来自客户端的下一个事件。阻塞调用，若在等待过程中，会话被用户关闭，则抛出SessionClosedException异常"""
        raise NotImplementedError

    def send_client_event(self, event):
        raise NotImplementedError

    def get_task_commands(self) -> list:
        raise NotImplementedError

    def close(self, nonblock=False):
        """Close current session

        :param bool nonblock: Don't block thread. Used in closing from backend.
        """
        if self._closed:
            return
        self._closed = True

        self.deferred_functions.reverse()
        while self.deferred_functions:
            func = self.deferred_functions.pop()
            try:
                func()
            except Exception as e:
                msg = "Error occurred when running deferred function %s" % func
                if isinstance(e, SessionException):
                    msg = "PyWebIO interactive functions cannot be called inside the deferred functions."
                logger.exception(msg)

    def closed(self) -> bool:
        return self._closed

    def on_task_exception(self):
        from ..output import toast, popup, put_error, PopupSize
        from . import run_js
        from . import info as session_info

        # log exception in server
        logger.exception('Unhandled error in pywebio app')

        try:
            toast_msg = "应用发生内部错误" if 'zh' in session_info.user_language else "An internal error occurred in the application"
            if type(self).debug:
                e_type, e_value, e_tb = sys.exc_info()
                lines = traceback.format_exception(e_type, e_value, e_tb)
                traceback_msg = ''.join(lines)
                popup(title=toast_msg, content=put_error(traceback_msg), size=PopupSize.LARGE)
                run_js("console.error(traceback_msg)", traceback_msg='Internal Server Error\n' + traceback_msg)
            else:
                toast(toast_msg, duration=1, color='error')
        except Exception:
            pass

    def register_callback(self, callback, **options):
        """ 向Session注册一个回调函数，返回回调id

        Session需要保证当收到前端发送的事件消息 ``{event: "callback"，task_id: 回调id, data:...}`` 时，
        ``callback`` 回调函数被执行， 并传入事件消息中的 ``data`` 字段值作为参数
        """
        raise NotImplementedError

    def defer_call(self, func):
        """设置会话结束时调用的函数。可以用于资源清理。
        在会话中可以多次调用 `defer_call()` ,会话结束后将会顺序执行设置的函数。

        :param func: 话结束时调用的函数
        """
        """设置会话结束时调用的函数。可以用于资源清理。"""
        self.deferred_functions.append(func)

    def need_keep_alive(self) -> bool:
        raise NotImplementedError


def get_session_info_from_headers(headers):
    """从Http请求头中获取会话信息

    :param headers: 字典类型的Http请求头
    :return: 表示会话信息的对象，属性有：

       * ``user_agent`` : 用户浏览器信息。可用字段见 https://github.com/selwin/python-user-agents#usage
       * ``user_language`` : 用户操作系统使用的语言
       * ``server_host`` : 当前会话的服务器host，包含域名和端口，端口为80时可以被省略
       * ``origin`` : 当前用户的页面地址. 包含 协议、主机、端口 部分. 比如 ``'http://localhost:8080'`` .
         可能为空，但保证当用户的页面地址不在当前服务器下(即 主机、端口部分和 ``server_host`` 不一致)时有值.
    """
    ua_str = headers.get('User-Agent', '')
    ua = user_agents.parse(ua_str)
    user_language = headers.get('Accept-Language', '').split(',', 1)[0].split(' ', 1)[0].split(';', 1)[0]
    server_host = headers.get('Host', '')
    origin = headers.get('Origin', '')
    session_info = dict(user_agent=ua, user_language=user_language,
                        server_host=server_host, origin=origin)
    return session_info
