"""从浏览器接收用户输入

本模块提供了一系列函数来从浏览器接收用户不同的形式的输入

输入函数大致分为两类，一类是单项输入::

    name = input("What's your name")
    print("Your name is %s" % name)

另一类是使用 `input_group` 的输入组::

    info = input_group("User info",[
      input('Input your name', name='name'),
      input('Input your age', name='age', type=NUMBER)
    ])
    print(info['name'], info['age'])

输入组中需要在每一项输入函数中提供 ``name`` 参数来用于在结果中标识不同输入项.

.. note::
   PyWebIO 根据是否在输入函数中传入 ``name`` 参数来判断输入函数是在 `input_group` 中还是被单独调用。
   所以当你想要单独调用一个输入函数时，请不要设置 ``name`` 参数；而在 `input_group` 中调用输入函数时，**务必提供** ``name`` 参数

"""

import logging
from base64 import b64decode
from collections.abc import Mapping
from typing import Coroutine

from .io_ctrl import single_input, input_control

logger = logging.getLogger(__name__)

TEXT = 'text'
NUMBER = "number"
FLOAT = "float"
PASSWORD = "password"
CHECKBOX = 'checkbox'
RADIO = 'radio'
SELECT = 'select'
TEXTAREA = 'textarea'

__all__ = ['TEXT', 'NUMBER', 'FLOAT', 'PASSWORD', 'CHECKBOX', 'RADIO', 'SELECT', 'TEXTAREA',
           'input', 'textarea', 'select', 'checkbox', 'radio', 'actions', 'file_upload', 'input_group']


def _parse_args(kwargs):
    """处理传给各类输入函数的原始参数，
    :return:（spec参数，valid_func）
    """
    # 对为None的参数忽略处理
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    kwargs.update(kwargs.get('other_html_attrs', {}))
    kwargs.pop('other_html_attrs', None)
    valid_func = kwargs.pop('valid_func', lambda _: None)
    return kwargs, valid_func


def input(label, type=TEXT, *, valid_func=None, name=None, value=None, placeholder=None, required=None,
          readonly=None, disabled=None, help_text=None, **other_html_attrs) -> Coroutine:
    r"""文本输入

    :param str label: 输入框标签
    :param str type: 输入类型. 可使用的常量：`TEXT` , `NUMBER` , `FLOAT`, `PASSWORD` , `TEXTAREA`
    :param Callable valid_func: 输入值校验函数. 如果提供，当用户输入完毕或提交表单后校验函数将被调用.
        ``valid_func`` 接收输入值作为参数，当输入值有效时，返回 ``None`` ，当输入值无效时，返回错误提示字符串. 比如::

            def check_age(age):
                if age>30:
                    return 'Too old'
                elif age<10:
                    return 'Too young'
            await input('Input your age', type=NUMBER, valid_func=check_age)

    :param name: 输入框的名字. 与 `input_group` 配合使用，用于在输入组的结果中标识不同输入项.  **在单个输入中，不可以设置该参数！**
    :param str value: 输入框的初始值
    :param str placeholder: 输入框的提示内容。提示内容会在输入框未输入值时以浅色字体显示在输入框中
    :param bool required: 当前输入是否为必填项
    :param bool readonly: 输入框是否为只读
    :param bool disabled: 输入框是否禁用。禁用的输入的值在提交表单时不会被提交
    :param str help_text: 输入框的帮助文本。帮助文本会以小号字体显示在输入框下方
    :param other_html_attrs: 在输入框上附加的额外html属性。参考： https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/input#%E5%B1%9E%E6%80%A7
    :return: 用户输入的值
    """

    item_spec, valid_func = _parse_args(locals())

    # 参数检查
    allowed_type = {TEXT, NUMBER, FLOAT, PASSWORD, TEXTAREA}
    assert type in allowed_type, 'Input type not allowed.'

    def preprocess_func(d):
        if type == NUMBER:
            d = int(d)
        elif type == FLOAT:
            d = float(d)

        return d

    return single_input(item_spec, valid_func, preprocess_func)


def textarea(label, rows=6, *, code=None, maxlength=None, minlength=None, valid_func=None, name=None, value=None,
             placeholder=None, required=None, readonly=None, disabled=None, help_text=None, **other_html_attrs):
    r"""文本输入域

    :param int rows: 输入文本的行数（显示的高度）。输入的文本超出设定值时会显示滚动条
    :param int maxlength: 允许用户输入的最大字符长度 (Unicode) 。未指定表示无限长度
    :param int minlength: 允许用户输入的最小字符长度(Unicode)
    :param dict code: 通过提供 `Codemirror <https://codemirror.net/>`_ 参数让文本输入域具有代码编辑器样式::

            res = await textarea('Text area', code={
                'mode': "python",
                'theme': 'darcula'
            })

        更多配置可以参考 https://codemirror.net/doc/manual.html#config
    :param - label, valid_func, name, value, placeholder, required, readonly, disabled, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 用户输入的文本
    """
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
            opt = dict(zip(('label', 'value', 'selected', 'disabled'), opt))
        else:
            opt = dict(value=opt, label=opt)
        opts_res.append(opt)

    return opts_res


def select(label, options, *, multiple=None, valid_func=None, name=None, value=None,
           placeholder=None, required=None, readonly=None, disabled=None, help_text=None,
           **other_html_attrs):
    r"""下拉选择框。默认单选，设置 multiple 参数后，可以多选。但都至少要选择一个选项。

    :param list options: 可选项列表。列表项的可用形式有：

        * dict: ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``
        * tuple or list: ``(label, value, [selected,] [disabled])``
        * 单值: 此时label和value使用相同的值

        注意：

        1. options 中的 value 最终会转换成字符串。 select 返回值也是字符串(或字符串列表)
        2. 若 ``multiple`` 选项不为 ``True`` 则可选项列表最多仅能有一项的 ``selected`` 为 ``True``。

    :param multiple: 是否可以多选. 默认单选
    :param - label, valid_func, name, value, placeholder, required, readonly, disabled, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 字符串/字符串列表。如果 ``multiple=True`` 时，返回用户选中的 options 中的值的列表；不设置 ``multiple`` 时，返回用户选中的 options 中的值
    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['options'] = _parse_select_options(options)
    item_spec['type'] = SELECT

    return single_input(item_spec, valid_func, lambda d: d)


def checkbox(label, options, *, inline=None, valid_func=None, name=None, value=None,
             placeholder=None, required=None, readonly=None, disabled=None, help_text=None, **other_html_attrs):
    r"""勾选选项。可以多选，也可以不选。

    :param list options: 可选项列表。格式与 `select` 函数的 ``options`` 参数含义一致
    :param bool inline: 是否将选项显示在一行上。默认每个选项单独占一行
    :param - label, valid_func, name, value, placeholder, required, readonly, disabled, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 用户选中的 options 中的值的列表。当用户没有勾选任何选项时，返回空列表
    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['options'] = _parse_select_options(options)
    item_spec['type'] = CHECKBOX

    return single_input(item_spec, valid_func, lambda d: d)


def radio(label, options, *, inline=None, valid_func=None, name=None, value=None,
          placeholder=None, required=None, readonly=None, disabled=None, help_text=None,
          **other_html_attrs):
    r"""单选选项

    :param list options: 可选项列表。格式与 `select` 函数的 ``options`` 参数含义一致
    :param bool inline: 是否将选项显示在一行上。默认每个选项单独占一行
    :param - label, valid_func, name, value, placeholder, required, readonly, disabled, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 用户选中的选项的值（字符串）
    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['options'] = _parse_select_options(options)
    item_spec['type'] = RADIO

    return single_input(item_spec, valid_func, lambda d: d)


def _parse_action_buttons(buttons):
    """
    :param label:
    :param actions: action 列表
    action 可用形式：
        {label:, value:, [disabled:]}
        (label, value, [disabled])
        value 单值，label等于value
    :return:
    """
    act_res = []
    for act in buttons:
        if isinstance(act, Mapping):
            assert 'value' in act and 'label' in act, 'actions item must have value and label key'
        elif isinstance(act, (list, tuple)):
            assert len(act) in (2, 3), 'actions item format error'
            act = dict(zip(('label', 'value', 'disabled'), act))
        else:
            act = dict(value=act, label=act)
        act_res.append(act)

    return act_res


def actions(label, buttons, name=None, help_text=None):
    r"""按钮选项。
    在浏览器上显示为一组按钮，与其他输入组件不同，用户点击按钮后会立即将整个表单提交，而其他输入组件则需要手动点击表单的"提交"按钮。

    :param list buttons: 选项列表。列表项的可用形式有：

        * dict: ``{label:选项标签, value:选项值, [disabled:是否禁止选择]}``
        * tuple or list: ``(label, value, [disabled])``
        * 单值: 此时label和value使用相同的值

    :param - label, name, help_text: 与 `input` 输入函数的同名参数含义一致
    :return: 用户点击的按钮的值
    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = 'actions'
    item_spec['buttons'] = _parse_action_buttons(buttons)

    return single_input(item_spec, valid_func, lambda d: d)


def file_upload(label, accept=None, name=None, placeholder='Choose file', help_text=None, **other_html_attrs):
    r"""文件上传。

    :param accept: 单值或列表, 表示可接受的文件类型。单值或列表项支持的形式有：

        * 以 ``.`` 字符开始的文件扩展名（例如：``.jpg, .png, .doc``）。
          注意：截止本文档编写之时，微信内置浏览器还不支持这种语法
        * 一个有效的 MIME 类型。
          例如： ``application/pdf`` 、 ``audio/*`` 表示音频文件、``video/*`` 表示视频文件、``image/*`` 表示图片文件
          参考 https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types

    :type accept: str or list
    :param - label, name, placeholder, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 表示用户文件的字典，格式为： ``{'filename': 文件名， 'content'：文件二进制数据(bytes object)}``
    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = 'file'

    def read_file(data):  # data: {'filename':, 'dataurl'}
        header, encoded = data['dataurl'].split(",", 1)
        data['content'] = b64decode(encoded)
        return data

    return single_input(item_spec, valid_func, read_file)


def input_group(label, inputs, valid_func=None):
    r"""输入组。向页面上展示一组输入

    :param str label: 输入组标签
    :param list inputs: 输入项列表。每一项为单项输入函数的返回值
    :param Callable valid_func: 输入组校验函数。
        函数签名：``callback(data) -> (name, error_msg)``
        ``valid_func`` 接收整个表单的值为参数，当校验表单值有效时，返回 ``None`` ，当某项输入值无效时，返回出错输入项的 ``name`` 值和错误提示. 比如::

            def check_form(data):
                if len(data['name']) > 6:
                    return ('name', '名字太长！')
                if data['age'] <= 0:
                    return ('age', '年龄不能为负数！')

            data = await input_group("Basic info",[
                input('Input your name', name='name'),
                input('Repeat your age', name='age', type=NUMBER)
            ], valid_func=check_form)

            print(data['name'], data['age'])

    :return: 返回一个 ``dict`` , 其键为输入项的 ``name`` 值，字典值为输入项的值
    """
    spec_inputs = []
    preprocess_funcs = {}
    item_valid_funcs = {}
    for single_input_return in inputs:
        try:
            single_input_return.send(None)
        except StopIteration as e:
            input_kwargs = e.args[0]
        except AttributeError:
            input_kwargs = single_input_return
        else:
            raise RuntimeError("Can't get kwargs from single input")

        assert all(k in input_kwargs for k in ('item_spec', 'preprocess_func', 'valid_func')), RuntimeError(
            "`inputs` value error in `input_group`. Did you forget to add `name` parameter in input function?")

        input_name = input_kwargs['item_spec']['name']
        preprocess_funcs[input_name] = input_kwargs['preprocess_func']
        item_valid_funcs[input_name] = input_kwargs['valid_func']
        spec_inputs.append(input_kwargs['item_spec'])

    if all('auto_focus' not in i for i in spec_inputs):  # 每一个输入项都没有设置autofocus参数
        for i in spec_inputs:
            text_inputs = {TEXT, NUMBER, PASSWORD, SELECT}  # todo update
            if i.get('type') in text_inputs:
                i['auto_focus'] = True
                break

    spec = dict(label=label, inputs=spec_inputs)
    return input_control(spec, preprocess_funcs=preprocess_funcs, item_valid_funcs=item_valid_funcs,
                         form_valid_funcs=valid_func)
