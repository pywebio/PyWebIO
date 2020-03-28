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


    由Backend调用：
        send_client_event
        get_task_commands
        close

    Task和Backend都可调用：
        closed

    .. note::
        后端Backend在相应on_session_close时关闭连接时，需要保证会话内的所有消息都传送到了客户端
    """

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
        :param on_session_close: Backend向Session注册的处理函数，当 Session task执行结束时调用 *
        :param kwargs:
        """
        raise NotImplementedError

    def send_task_command(self, command):
        raise NotImplementedError

    def next_client_event(self) -> dict:
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
