"""
输入输出的底层实现函数


"""
import logging

from .session import chose_impl, next_client_event, get_current_task_id, get_current_session

logger = logging.getLogger(__name__)


def send_msg(cmd, spec=None):
    msg = dict(command=cmd, spec=spec, task_id=get_current_task_id())
    get_current_session().send_task_command(msg)


@chose_impl
def single_input(item_spec, valid_func, preprocess_func):
    """
    Note: 鲁棒性在上层完成
    将单个input构造成input_group，并获取返回值
    :param item_spec: 单个输入项的参数 'name' must in item_spec， 参数一定已经验证通过
    :param valid_func: Not None
    :param preprocess_func: Not None
    """
    if item_spec.get('name') is None:  # single input
        item_spec['name'] = 'data'
    else:  # as input_group item
        return dict(item_spec=item_spec, valid_func=valid_func, preprocess_func=preprocess_func)

    label = item_spec['label']
    name = item_spec['name']
    # todo 是否可以原地修改spec
    item_spec['label'] = ''

    item_spec.setdefault('auto_focus', True)  # 如果没有设置autofocus参数，则开启参数  todo CHECKBOX, RADIO 特殊处理

    spec = dict(label=label, inputs=[item_spec])
    data = yield input_control(spec, {name: preprocess_func}, {name: valid_func})
    return data[name]


@chose_impl
def input_control(spec, preprocess_funcs, item_valid_funcs, form_valid_funcs=None):
    """
    发送input命令，监听事件，验证输入项，返回结果
    :param spec:
    :param preprocess_funcs: keys 严格等于 spec中的name集合
    :param item_valid_funcs: keys 严格等于 spec中的name集合
    :param form_valid_funcs:
    :return:
    """
    send_msg('input_group', spec)

    data = yield input_event_handle(item_valid_funcs, form_valid_funcs, preprocess_funcs)

    send_msg('destroy_form')
    return data


def check_item(name, data, valid_func, preprocess_func):
    try:
        data = preprocess_func(data)
        error_msg = valid_func(data)
    except Exception as e:
        logger.warning('Get %r in valid_func for name:"%s"', e, name)
        error_msg = '字段内容不合法'
    if error_msg is not None:
        send_msg('update_input', dict(target_name=name, attributes={
            'valid_status': False,
            'invalid_feedback': error_msg
        }))
        return False
    return True


@chose_impl
def input_event_handle(item_valid_funcs, form_valid_funcs, preprocess_funcs):
    """
    根据提供的校验函数处理表单事件
    :param item_valid_funcs: map(name -> valid_func)  valid_func 为 None 时，不进行验证
                        valid_func: callback(data) -> error_msg or None
    :param form_valid_funcs: callback(data) -> (name, error_msg) or None
    :param preprocess_funcs:
    :return:
    """
    while True:
        event = yield next_client_event()
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
        elif event_name == 'from_cancel':
            data = None
            break
        else:
            logger.warning("Unhandled Event: %s", event)

    return data


def output_register_callback(callback, **options):
    task_id = get_current_session().register_callback(callback, **options)
    return task_id
