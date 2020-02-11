import tornado.websocket
import time, json
from collections import defaultdict
from .framework import Future, Msg, Global
from collections.abc import Iterable, Mapping, Sequence

import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    Global.active_ws.inactive_coro_instances.append(coro)


def send_msg(cmd, spec=None):
    msg = dict(command=cmd, spec=spec, coro_id=Global.active_coro_id)
    Global.active_ws.write_message(json.dumps(msg))


def get_response(cmd, spec):
    send_msg(cmd, spec)
    response_msg = yield from Future()
    return response_msg


TEXT = 'text'
NUMBER = "number"
PASSWORD = "password"
CHECKBOX = 'checkbox'
RADIO = 'radio'
SELECT = 'select'


def _input_event_handle(valid_funcs, whole_valid_func=None):
    """
    根据提供的校验函数处理表单事件
    :param valid_funcs: map(name -> valid_func)  valid_func 为 None 时，不进行验证
                        valid_func: callback(data) -> error_msg
    :param whole_valid_func: callback(data) -> (name, error_msg)
    :return:
    """
    while True:
        event = yield
        event_name, event_data = event['event'], event['data']
        if event_name == 'input_event':
            input_event = event_data['event_name']
            if input_event == 'on_blur':
                onblur_name = event_data['name']
                valid_func = valid_funcs.get(onblur_name)
                if valid_func is None:
                    continue
                error_msg = valid_func(event_data['value'])
                if error_msg is not None:
                    send_msg('update_input', dict(target_name=onblur_name, attributes={
                        'valid_status': False,
                        'invalid_feedback': error_msg
                    }))
        elif event_name == 'from_submit':
            all_valid = True

            # 调用输入项验证函数进行校验
            for name, valid_func in valid_funcs.items():
                if valid_func is None:
                    continue
                error_msg = valid_func(event_data[name])
                if error_msg is not None:
                    all_valid = False
                    send_msg('update_input', dict(target_name=name, attributes={
                        'valid_status': False,
                        'invalid_feedback': error_msg
                    }))

            # 调用表单验证函数进行校验
            if whole_valid_func:
                v_res = whole_valid_func(event_data)
                if v_res is not None:
                    all_valid = False
                    onblur_name, error_msg = v_res
                    send_msg('update_input', dict(target_name=onblur_name, attributes={
                        'valid_status': False,
                        'invalid_feedback': error_msg
                    }))

            if all_valid:
                break

    return event['data']


def _make_input_spec(label, type, name, valid_func=None, multiple=None, inline=None, other_html_attrs=None,
                     **other_kwargs):
    """
    校验传入input函数和select函数的参数
    生成input_group消息中spec inputs参数列表项
    支持的input类型 TEXT, NUMBER, PASSWORD, CHECKBOX, RADIO, SELECT
    """
    allowed_type = {TEXT, NUMBER, PASSWORD, CHECKBOX, RADIO, SELECT}
    assert type in allowed_type, 'Input type not allowed.'

    input_item = other_kwargs
    input_item.update(other_html_attrs or {})
    input_item.update(dict(label=label, type=type, name=name))

    if valid_func is not None and type in (CHECKBOX, RADIO):  # CHECKBOX, RADIO 不支持valid_func参数
        logger.warning('valid_func can\'t be used when type in (CHECKBOX, RADIO)')

    if inline is not None and type not in {CHECKBOX, RADIO}:
        logger.warning('inline 只能用于 CHECKBOX, RADIO type')
    elif inline is not None:
        input_item['inline'] = inline

    if multiple is not None and type != SELECT:
        logger.warning('multiple 参数只能用于SELECT type')
    elif multiple is not None:
        input_item['multiple'] = multiple

    if type in {CHECKBOX, RADIO, SELECT}:
        assert 'options' in input_item, 'Input type not allowed.'
        assert isinstance(input_item['options'], Iterable), 'options must be list type'
        # option 可用形式：
        # {value:, label:, [selected:,] [disabled:]}
        # (value, label, [selected,] [disabled])
        # value 单值，label等于value
        opts = input_item['options']
        opts_res = []
        for opt in opts:
            if isinstance(opt, Mapping):
                assert 'value' in opt and 'label' in opt, 'options item must have value and label key'
            elif isinstance(opt, list):
                assert len(opt) > 1 and len(opt) <= 4, 'options item format error'
                opt = dict(zip(('value', 'label', 'selected', 'disabled'), opt))
            else:
                opt = dict(value=opt, label=opt)
            opts_res.append(opt)

        input_item['options'] = opts_res

    # todo spec参数中，为默认值的可以不发送
    return input_item


def input(label, type=TEXT, *, valid_func=None, name='data', value='', placeholder='', required=False, readonly=False,
          disabled=False, **other_html_attrs):
    input_kwargs = dict(locals())
    input_kwargs['label'] = ''
    input_kwargs['__name__'] = input.__name__
    input_kwargs.setdefault('autofocus', True)  # 如果没有设置autofocus参数，则开启参数

    # 参数检查
    allowed_type = {TEXT, NUMBER, PASSWORD}
    assert type in allowed_type, 'Input type not allowed.'

    data = yield from input_group(label=label, inputs=[input_kwargs])
    return data[name]


def select(label, options, type=SELECT, *, multiple=None, valid_func=None, name='data', value='', placeholder='',
           required=False, readonly=False, disabled=False, inline=None, **other_html_attrs):
    """
    参数值为None表示不指定，使用默认值

    :param label:
    :param options: option 列表
        option 可用形式：
        {value:, label:, [selected:,] [disabled:]}
        (value, label, [selected,] [disabled])
        value 单值，label等于value
    :param type:
    :param multiple:
    :param valid_func:
    :param name:
    :param value:
    :param placeholder:
    :param required:
    :param readonly:
    :param disabled:
    :param inline:
    :param other_html_attrs:
    :return:
    """
    input_kwargs = dict(locals())
    input_kwargs['label'] = ''
    input_kwargs['__name__'] = select.__name__

    allowed_type = {CHECKBOX, RADIO, SELECT}
    assert type in allowed_type, 'Input type not allowed.'

    data = yield from input_group(label=label, inputs=[input_kwargs])
    return data[name]


def _make_actions_input_spec(label, actions, name):
    """
    :param label:
    :param actions: action 列表
    action 可用形式：
        {value:, label:, [disabled:]}
        (value, label, [disabled])
        value 单值，label等于value
    :return:
    """
    act_res = []
    for act in actions:
        if isinstance(act, Mapping):
            assert 'value' in act and 'label' in act, 'actions item must have value and label key'
        elif isinstance(act, Sequence):
            assert len(act) in (2, 3), 'actions item format error'
            act = dict(zip(('value', 'label', 'disabled'), act))
        else:
            act = dict(value=act, label=act)
        act_res.append(act)

    input_item = dict(type='buttons', label=label, name=name, actions=actions)
    return input_item


def actions(label, actions, name='data'):
    """
    选择一个动作。UI为多个按钮，点击后会将整个表单提交
    :param label:
    :param actions: action 列表
    action 可用形式：
        {value:, label:, [disabled:]}
        (value, label, [disabled])
        value 单值，label等于value

    实现方式：
    多个type=submit的input组成
    [
        <button data-name value>label</button>,
        ...
    ]
    """
    input_kwargs = dict(label='', actions=actions, name=name)
    input_kwargs['__name__'] = select.__name__
    data = yield from input_group(label=label, inputs=[input_kwargs])
    return data[name]


def input_group(label, inputs, valid_func=None):
    """
    :param label:
    :param inputs: list of generator or dict， dict的话，需要多加一项 __name__ 为当前函数名
    :param valid_func: callback(data) -> (name, error_msg)
    :return:
    """
    make_spec_funcs = {
        actions.__name__: _make_actions_input_spec,
        input.__name__: _make_input_spec,
        select.__name__: _make_input_spec
    }

    item_valid_funcs = {}
    spec_inputs = []
    for input_g in inputs:
        if isinstance(input_g, dict):
            func_name = input_g.pop('__name__')
            input_kwargs = input_g
        else:
            input_kwargs = dict(input_g.gi_frame.f_locals)  # 拷贝一份，不可以对locals进行修改
            func_name = input_g.__name__

        input_name = input_kwargs['name']
        item_valid_funcs[input_name] = input_kwargs['valid_func']
        input_item = make_spec_funcs[func_name](**input_kwargs)
        spec_inputs.append(input_item)

    if all('autofocus' not in i for i in spec_inputs):  # 每一个输入项都没有设置autofocus参数
        for i in spec_inputs:
            text_inputs = {TEXT, NUMBER, PASSWORD}  # todo update
            if i.get('type') in text_inputs:
                i['autofocus'] = True
                break

    send_msg('input_group', dict(label=label, inputs=spec_inputs))
    data = yield from _input_event_handle(item_valid_funcs, valid_func)
    send_msg('destroy_form')
    return data


def ctrl_coro(ctrl_info):
    msg = dict(command="ctrl", spec=ctrl_info)
    Global.active_ws.write_message(json.dumps(msg))


def text_print(text, *, ws=None):
    msg = dict(command="output", spec=dict(content=text, type='text'))
    (ws or Global.active_ws).write_message(json.dumps(msg))


def json_print(obj):
    text = "```\n%s\n```" % json.dumps(obj, indent=4, ensure_ascii=False)
    text_print(text)
