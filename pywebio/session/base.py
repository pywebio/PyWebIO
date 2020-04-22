class AbstractSession:
    """
    会话对象，由Backend创建

    由Task在当前Session上下文中调用：
        get_current_session
        get_current_task_id

        send_task_command
        next_client_event
        on_task_exception
        register_callback

        defer_call

    由Backend调用：
        send_client_event
        get_task_commands
        close

    Task和Backend都可调用：
        closed
        active_session_count


    Session是不同的后端Backend与协程交互的桥梁：
        后端Backend在接收到用户浏览器的数据后，会通过调用 ``send_client_event`` 来通知会话，进而由Session驱动协程的运行。
        Task内在调用输入输出函数后，会调用 ``send_task_command`` 向会话发送输入输出消息指令， Session将其保存并留给后端Backend处理。
    """

    @staticmethod
    def active_session_count() -> int:
        raise NotImplementedError

    @staticmethod
    def get_current_session() -> "AbstractSession":
        raise NotImplementedError

    @staticmethod
    def get_current_task_id():
        raise NotImplementedError

    def __init__(self, target, on_task_command=None, on_session_close=None, **kwargs):
        """
        :param target:
        :param on_task_command: Backend向ession注册的处理函数，当 Session 收到task发送的command时调用
        :param on_session_close: Backend向Session注册的处理函数，当 Session task 执行结束时调用 *
        :param kwargs:

        .. note::
            后端Backend在相应on_session_close时关闭连接时，需要保证会话内的所有消息都传送到了客户端
        """
        raise NotImplementedError

    def send_task_command(self, command):
        raise NotImplementedError

    def next_client_event(self) -> dict:
        """获取来自客户端的下一个事件。阻塞调用，若在等待过程中，会话被用户关闭，则抛出SessionClosedException异常"""
        raise NotImplementedError

    def send_client_event(self, event):
        raise NotImplementedError

    def get_task_commands(self) -> list:
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def closed(self) -> bool:
        raise NotImplementedError

    def on_task_exception(self):
        raise NotImplementedError

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
        raise NotImplementedError