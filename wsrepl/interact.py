import json
import logging
from collections.abc import Mapping
from base64 import b64decode
from .framework import Global
from .input_ctrl import send_msg, single_input, input_control

logger = logging.getLogger(__name__)





TEXT = 'text'
NUMBER = "number"
PASSWORD = "password"
CHECKBOX = 'checkbox'
RADIO = 'radio'
SELECT = 'select'
TEXTAREA = 'textarea'


def _parse_args(kwargs):
    """处理传给各类input函数的原始参数，
    :return:（spec参数，valid_func）
    """
    # 对为None的参数忽律处理
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    kwargs.update(kwargs.get('other_html_attrs', {}))
    kwargs.pop('other_html_attrs', None)
    valid_func = kwargs.pop('valid_func', lambda _: None)
    return kwargs, valid_func


def input(label, type=TEXT, *, valid_func=None, name='data', value=None, placeholder=None, required=None,
          readonly=None, disabled=None, help_text=None, **other_html_attrs):
    """可以通过datalist提供候选输入"""
    item_spec, valid_func = _parse_args(locals())

    # 参数检查
    allowed_type = {TEXT, NUMBER, PASSWORD, TEXTAREA}
    assert type in allowed_type, 'Input type not allowed.'

    def preprocess_func(d):
        if type == NUMBER:
            return int(d)
        return d

    return single_input(item_spec, valid_func, preprocess_func)


def textarea(label, rows=6, *, code=None, valid_func=None, name='data', value=None, placeholder=None, required=None,
             maxlength=None, minlength=None, readonly=None, disabled=None, help_text=None, **other_html_attrs):
    """提供codemirror参数产生代码输入样式"""
    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = TEXTAREA

    return single_input(item_spec, valid_func, lambda d: d)


def _parse_select_options(options):
    # option 可用形式：
    # {value:, label:, [selected:,] [disabled:]}
    # (value, label, [selected,] [disabled])
    # value 单值，label等于value
    opts_res = []
    for opt in options:
        if isinstance(opt, Mapping):
            assert 'value' in opt and 'label' in opt, 'options item must have value and label key'
        elif isinstance(opt, list):
            assert len(opt) > 1 and len(opt) <= 4, 'options item format error'
            opt = dict(zip(('value', 'label', 'selected', 'disabled'), opt))
        else:
            opt = dict(value=opt, label=opt)
        opts_res.append(opt)

    return opts_res


def select(label, options, type=SELECT, *, multiple=None, valid_func=None, name='data', value=None,
           placeholder=None, required=None, readonly=None, disabled=None, inline=None, help_text=None,
           **other_html_attrs):
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
    item_spec, valid_func = _parse_args(locals())
    item_spec['options'] = _parse_select_options(options)

    allowed_type = {CHECKBOX, RADIO, SELECT}
    assert type in allowed_type, 'Input type not allowed.'

    if inline is not None and type not in {CHECKBOX, RADIO}:
        del item_spec['inline']
        logger.warning('inline 只能用于 CHECKBOX, RADIO type, now type:%s', type)

    if multiple is not None and type != SELECT:
        del item_spec['multiple']
        logger.warning('multiple 参数只能用于SELECT type, now type:%s', type)

    return single_input(item_spec, valid_func, lambda d: d)


def _parse_action_buttons(buttons):
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
    for act in buttons:
        if isinstance(act, Mapping):
            assert 'value' in act and 'label' in act, 'actions item must have value and label key'
        elif isinstance(act, list):
            assert len(act) in (2, 3), 'actions item format error'
            act = dict(zip(('value', 'label', 'disabled'), act))
        else:
            act = dict(value=act, label=act)
        act_res.append(act)

    return act_res


def actions(label, buttons, name='data', help_text=None):
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
    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = 'actions'
    item_spec['buttons'] = _parse_action_buttons(buttons)

    return single_input(item_spec, valid_func, lambda d: d)


def file_upload(label, accept=None, name='data', placeholder='Choose file', help_text=None, **other_html_attrs):
    """
    :param label:
    :param accept: 表明服务器端可接受的文件类型；该属性的值必须为一个逗号分割的列表,包含了多个唯一的内容类型声明：
        以 STOP 字符 (U+002E) 开始的文件扩展名。（例如：".jpg,.png,.doc"）
        一个有效的 MIME 类型，但没有扩展名
        audio/* 表示音频文件
        video/* 表示视频文件
        image/* 表示图片文件
    :param placeholder:
    :param help_text:
    :param other_html_attrs:
    :return:
    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = 'file'

    def read_file(data):  # data: {'filename':, 'dataurl'}
        header, encoded = data['dataurl'].split(",", 1)
        data['content'] = b64decode(encoded)
        del data['dataurl']
        return data

    return single_input(item_spec, valid_func, read_file)

def confirm():
    pass

def input_group(label, inputs, valid_func=None):
    """
    :param label:
    :param inputs: list of single_input coro
    :param valid_func: callback(data) -> (name, error_msg)
    :return:
    """
    spec_inputs = []
    preprocess_funcs = {}
    item_valid_funcs = {}
    for single_input_cr in inputs:
        input_kwargs = dict(single_input_cr.cr_frame.f_locals)  # 拷贝一份，不可以对locals进行修改
        single_input_cr.close()
        input_name = input_kwargs['item_spec']['name']
        preprocess_funcs[input_name] = input_kwargs['preprocess_func']
        item_valid_funcs[input_name] = input_kwargs['valid_func']
        spec_inputs.append(input_kwargs['item_spec'])

    # def add_autofocus(spec_inputs):
    if all('autofocus' not in i for i in spec_inputs):  # 每一个输入项都没有设置autofocus参数
        for i in spec_inputs:
            text_inputs = {TEXT, NUMBER, PASSWORD, SELECT}  # todo update
            if i.get('type') in text_inputs:
                i['autofocus'] = True
                break

    spec = dict(label=label, inputs=spec_inputs)
    return input_control(spec, preprocess_funcs=preprocess_funcs, item_valid_funcs=item_valid_funcs,
                         form_valid_funcs=valid_func)
