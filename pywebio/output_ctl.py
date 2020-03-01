from .input_ctrl import send_msg, single_input, input_control, next_event, run_async
import asyncio
import inspect
from .framework import Global, Task


def register_callback(callback, save, mutex_mode):
    """
    为输出区显示的控件注册回调函数

    原理：
        向框架注册一个新协程，在协程内对回调函数进行调用 callback(widget_data, save)
        协程会在用户与控件交互时触发

    :return: 协程id
    """

    async def callback_coro():
        while True:
            event = await next_event()
            assert event['event'] == 'callback'
            coro = None
            if asyncio.iscoroutinefunction(callback):
                coro = callback(event['data'], save)
            elif inspect.isgeneratorfunction(callback):
                coro = asyncio.coroutine(callback)(save, event['data'])
            else:
                try:
                    callback(event['data'], save)
                except:
                    Global.active_ws.on_coro_error()

            if coro is not None:
                if mutex_mode:
                    await coro
                else:
                    run_async(coro)

    callback_task = Task(callback_coro(), Global.active_ws)
    callback_task.coro.send(None)  # 激活，Non't callback.step() ,导致嵌套调用step  todo 与inactive_coro_instances整合
    Global.active_ws.coros[callback_task.coro_id] = callback_task

    return callback_task.coro_id
