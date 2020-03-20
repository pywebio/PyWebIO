import asyncio
import inspect
import logging

from .session.asyncbased import WebIOFuture, AsyncBasedSession, Task
from .ioloop import run_async

logger = logging.getLogger(__name__)


def send_msg(cmd, spec=None):
    msg = dict(command=cmd, spec=spec, coro_id=AsyncBasedSession.get_current_task_id())
    AsyncBasedSession.get_current_session().send_task_message(msg)


async def next_event():
    res = await AsyncBasedSession.get_current_session().next_client_event()
    return res


async def single_input(item_spec, valid_func, preprocess_func):
    """
    Note: 鲁棒性在上层完成
    将单个input构造成input_group，并获取返回值
    :param item_spec: 单个输入项的参数 'name' must in item_spec， 参数一定已经验证通过
    :param valid_func: Not None
    :param preprocess_func: Not None
    """
    label = item_spec['label']
    name = item_spec['name']
    # todo 是否可以原地修改spec
    item_spec['label'] = ''

    item_spec.setdefault('auto_focus', True)  # 如果没有设置autofocus参数，则开启参数  todo CHECKBOX, RADIO 特殊处理

    spec = dict(label=label, inputs=[item_spec])

    data = await input_control(spec, {name: preprocess_func}, {name: valid_func})
    return data[name]


async def input_control(spec, preprocess_funcs, item_valid_funcs, form_valid_funcs=None):
    """
    发送input命令，监听事件，验证输入项，返回结果
    :param spec:
    :param preprocess_funcs: keys 严格等于 spec中的name集合
    :param item_valid_funcs: keys 严格等于 spec中的name集合
    :param form_valid_funcs:
    :return:
    """
    send_msg('input_group', spec)

    data = await input_event_handle(item_valid_funcs, form_valid_funcs, preprocess_funcs)

    send_msg('destroy_form')
    return data


def check_item(name, data, valid_func, preprocess_func):
    try:
        data = preprocess_func(data)
        error_msg = valid_func(data)
    except:
        # todo log warning
        error_msg = '字段内容不合法'
    if error_msg is not None:
        send_msg('update_input', dict(target_name=name, attributes={
            'valid_status': False,
            'invalid_feedback': error_msg
        }))
        return False
    return True


async def input_event_handle(item_valid_funcs, form_valid_funcs, preprocess_funcs):
    """
    根据提供的校验函数处理表单事件
    :param item_valid_funcs: map(name -> valid_func)  valid_func 为 None 时，不进行验证
                        valid_func: callback(data) -> error_msg or None
    :param form_valid_funcs: callback(data) -> (name, error_msg) or None
    :param preprocess_funcs:
    :return:
    """
    while True:
        event = await next_event()
        event_name, event_data = event['event'], event['data']
        if event_name == 'input_event':
            input_event = event_data['event_name']
            if input_event == 'blur':
                onblur_name = event_data['name']
                check_item(onblur_name, event_data['value'], item_valid_funcs[onblur_name],
                           preprocess_funcs[onblur_name])

        elif event_name == 'from_submit':
            all_valid = True

            # 调用输入项验证函数进行校验
            for name, valid_func in item_valid_funcs.items():
                if not check_item(name, event_data[name], valid_func, preprocess_funcs[name]):
                    all_valid = False

            if all_valid:  # todo 减少preprocess_funcs[name]调用次数
                data = {name: preprocess_funcs[name](val) for name, val in event_data.items()}
                # 调用表单验证函数进行校验
                if form_valid_funcs:
                    v_res = form_valid_funcs(data)
                    if v_res is not None:
                        all_valid = False
                        onblur_name, error_msg = v_res
                        send_msg('update_input', dict(target_name=onblur_name, attributes={
                            'valid_status': False,
                            'invalid_feedback': error_msg
                        }))

            if all_valid:
                break
        else:
            logger.warning("Unhandled Event: %s", event)

    return data


def output_register_callback(callback, save, mutex_mode):
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
                    AsyncBasedSession.get_current_session().on_task_exception()

            if coro is not None:
                if mutex_mode:
                    await coro
                else:
                    run_async(coro)

    callback_task = Task(callback_coro(), AsyncBasedSession.get_current_session())
    callback_task.coro.send(None)  # 激活，Non't callback.step() ,导致嵌套调用step  todo 与inactive_coro_instances整合
    AsyncBasedSession.get_current_session().coros[callback_task.coro_id] = callback_task

    return callback_task.coro_id
