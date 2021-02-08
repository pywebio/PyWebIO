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

输入默认可以忽略，如果需要用户必须提供值，则需要在输入函数中传入 ``required=True`` (部分输入函数不支持 ``required`` 参数)

函数清单
------------

.. list-table::

   * - 函数
     - 简介

   * - `input <pywebio.input.input>`
     - 文本输入

   * - `textarea <pywebio.input.textarea>`
     - 多行文本输入

   * - `select <pywebio.input.select>`
     - 下拉选择框

   * - `checkbox <pywebio.input.checkbox>`
     - 勾选选项

   * - `radio <pywebio.input.radio>`
     - 单选选项

   * - `actions <pywebio.input.actions>`
     - 按钮选项

   * - `file_upload <pywebio.input.file_upload>`
     - 文件上传

   * - `input_group <pywebio.input.input_group>`
     - 输入组


函数文档
------------
"""

import logging
from base64 import b64decode
from collections.abc import Mapping
from functools import partial

from .io_ctrl import single_input, input_control, output_register_callback
from .session import get_current_session, get_current_task_id
from .utils import Setter, is_html_safe_value

logger = logging.getLogger(__name__)

TEXT = 'text'
NUMBER = "number"
FLOAT = "float"
PASSWORD = "password"
URL = "url"
DATE = "date"
TIME = "time"

CHECKBOX = 'checkbox'
RADIO = 'radio'
SELECT = 'select'
TEXTAREA = 'textarea'

__all__ = ['TEXT', 'NUMBER', 'FLOAT', 'PASSWORD', 'URL', 'DATE', 'TIME', 'input', 'textarea', 'select',
           'checkbox', 'radio', 'actions', 'file_upload', 'input_group']


def _parse_args(kwargs, excludes=()):
    """处理传给各类输入函数的原始参数

     - excludes: 排除的参数
     - 对为None的参数忽略处理

    :return:（spec参数，valid_func）
    """
    kwargs = {k: v for k, v in kwargs.items() if v is not None and k not in excludes}
    assert is_html_safe_value(kwargs.get('name', '')), '`name` can only contains a-z、A-Z、0-9、_、-'
    kwargs.update(kwargs.get('other_html_attrs', {}))
    kwargs.pop('other_html_attrs', None)
    valid_func = kwargs.pop('validate', lambda _: None)
    return kwargs, valid_func


def input(label='', type=TEXT, *, validate=None, name=None, value=None, action=None, placeholder=None, required=None,
          readonly=None, datalist=None, help_text=None, **other_html_attrs):
    r"""文本输入

    :param str label: 输入框标签
    :param str type: 输入类型. 可使用的常量：`TEXT` , `NUMBER` , `FLOAT` , `PASSWORD` , `URL` , `DATE` , `TIME`

       其中 `DATE` , `TIME` 类型在某些浏览器上不被支持，详情见 https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input#Browser_compatibility
    :param callable validate: 输入值校验函数. 如果提供，当用户输入完毕或提交表单后校验函数将被调用.
        ``validate`` 接收输入值作为参数，当输入值有效时，返回 ``None`` ，当输入值无效时，返回错误提示字符串. 比如:

        .. exportable-codeblock::
            :name: input-valid-func
            :summary: `input()` 输入值校验

            def check_age(age):
                if age>30:
                    return 'Too old'
                elif age<10:
                    return 'Too young'
            input('Input your age', type=NUMBER, validate=check_age)

    :param str name: 输入框的名字. 与 `input_group` 配合使用，用于在输入组的结果中标识不同输入项.  **在单个输入中，不可以设置该参数！**
    :param str value: 输入框的初始值
    :type action: tuple(label:str, callback:callable)
    :param action: 在输入框右侧显示一个按钮，可通过点击按钮为输入框设置值。

        ``label`` 为按钮的显示文本， ``callback`` 为按钮点击的回调函数。

        回调函数需要接收一个 ``set_value`` 位置参数， ``set_value`` 是一个可调用对象，接受单参数调用和双参数调用。

        单参数调用时，签名为 ``set_value(value:str)`` ，调用set_value即可将表单项的值设置为传入的 ``value`` 参数。

        双参数调用时，签名为 ``set_value(value:any, label:str)`` ，其中：

         * ``value`` 参数为最终输入项的返回值，可以为任意Python对象，并不会传递给用户浏览器
         * ``label`` 参数用于显示在用户表单项上

        使用双参数调用 ``set_value`` 后，用户表单项会变为只读状态。

        双参数调用的使用场景为：表单项的值通过回调动态生成，同时希望用户表单显示的和实际提交的数据不同(例如表单项上可以显示更人性化的内容，而表单项的值则可以保存更方便被处理的对象)

        使用示例:

        .. exportable-codeblock::
            :name: input-action
            :summary: `input()`使用action参数动态设置表单项的值

            import time
            def set_now_ts(set_value):
                set_value(int(time.time()))

            ts = input('Timestamp', type=NUMBER, action=('Now', set_now_ts))
            put_text('Timestamp:', ts)  # ..demo-only
            ## ----
            from datetime import date,timedelta
            def select_date(set_value):
                with popup('Select Date'):
                    put_buttons(['Today'], onclick=[lambda: set_value(date.today(), 'Today')])
                    put_buttons(['Yesterday'], onclick=[lambda: set_value(date.today() - timedelta(days=1), 'Yesterday')])

            d = input('Date', action=('Select', select_date), readonly=True)
            put_text(type(d), d)

        Note: 当使用 :ref:`基于协程的会话实现 <coroutine_based_session>` 时，回调函数 ``callback`` 可以为协程函数.

    :param str placeholder: 输入框的提示内容。提示内容会在输入框未输入值时以浅色字体显示在输入框中
    :param bool required: 当前输入是否为必填项
    :param bool readonly: 输入框是否为只读
    :param list datalist: 输入建议内容列表，在页面上的显示效果为下拉候选列表，用户可以忽略建议内容列表而输入其他内容。仅当输入类型 ``type`` 为 `TEXT` 时可用
    :param str help_text: 输入框的帮助文本。帮助文本会以小号字体显示在输入框下方
    :param other_html_attrs: 在输入框上附加的额外html属性。参考： https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/input#%E5%B1%9E%E6%80%A7
    :return: 用户输入的值
    """

    item_spec, valid_func = _parse_args(locals(), excludes=('action',))

    # 参数检查
    allowed_type = {TEXT, NUMBER, FLOAT, PASSWORD, URL, DATE, TIME}
    assert type in allowed_type, 'Input type not allowed.'

    if type == FLOAT:
        item_spec['type'] = TEXT

    value_setter = None
    if action:
        label, callback = action
        task_id = get_current_task_id()

        value_setter = Setter()

        def _set_value(value, label=value_setter):
            spec = {
                'target_name': item_spec.get('name', 'data'),
                'attributes': {'value': value}
            }
            if label is not value_setter:
                value_setter.label = label
                spec['attributes']['value'] = label
                spec['attributes']['readonly'] = True
            value_setter.value = value
            msg = dict(command='update_input', task_id=task_id, spec=spec)
            get_current_session().send_task_command(msg)

        callback_id = output_register_callback(lambda _: callback(_set_value))
        item_spec['action'] = dict(label=label, callback_id=callback_id)

    def preprocess_func(d):  # 将用户提交的原始数据进行转换
        if value_setter is not None and value_setter.label == d:
            return value_setter.value

        if type == NUMBER:
            d = int(d)
        elif type == FLOAT:
            d = float(d)

        return d

    return single_input(item_spec, valid_func, preprocess_func)


def textarea(label='', *, rows=6, code=None, maxlength=None, minlength=None, validate=None, name=None, value=None,
             placeholder=None, required=None, readonly=None, help_text=None, **other_html_attrs):
    r"""文本输入域（多行文本输入）

    :param int rows: 输入框的最多可显示的文本的行数，内容超出时会显示滚动条
    :param int maxlength: 最大允许用户输入的字符长度 (Unicode) 。未指定表示无限长度
    :param int minlength: 最少需要用户输入的字符长度(Unicode)
    :param dict code: 通过提供 `Codemirror <https://codemirror.net/>`_ 参数让文本输入域具有代码编辑器样式:

        .. exportable-codeblock::
            :name: textarea-code
            :summary: `textarea()`代码编辑

            res = textarea('Text area', code={
                'mode': "python",
                'theme': 'darcula'
            })
            put_code(res, language='python')  # ..demo-only

        :ref:`这里 <codemirror_options>` 列举了一些常用的Codemirror选项
    :param - label, validate, name, value, placeholder, required, readonly, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 用户输入的文本
    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = TEXTAREA

    return single_input(item_spec, valid_func, lambda d: d)


def _parse_select_options(options):
    # 转换 select、checkbox、radio函数中的 options 参数为统一的格式
    # option 可用形式：
    # {value:, label:, [selected:,] [disabled:]}
    # (value, label, [selected,] [disabled])
    # value 单值，label等于value
    opts_res = []
    for opt in options:
        if isinstance(opt, Mapping):
            assert 'value' in opt and 'label' in opt, 'options item must have value and label key'
        elif isinstance(opt, (list, tuple)):
            assert len(opt) > 1 and len(opt) <= 4, 'options item format error'
            opt = dict(zip(('label', 'value', 'selected', 'disabled'), opt))
        else:
            opt = dict(value=opt, label=opt)
        opt['value'] = opt['value']
        opts_res.append(opt)

    return opts_res


def _set_options_selected(options, value):
    """使用value为options的项设置selected"""
    if not isinstance(value, (list, tuple)):
        value = [value]
    for opt in options:
        if opt['value'] in value:
            opt['selected'] = True
    return options


def select(label='', options=None, *, multiple=None, validate=None, name=None, value=None, required=None,
           help_text=None, **other_html_attrs):
    r"""下拉选择框。

    默认单选，可以通过设置 ``multiple`` 参数来允许多选

    :param list options: 可选项列表。列表项的可用形式有：

        * dict: ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``
        * tuple or list: ``(label, value, [selected,] [disabled])``
        * 单值: 此时label和value使用相同的值

        注意：

        1. ``options`` 中的 ``value`` 可以为任意可JSON序列化对象
        2. 若 ``multiple`` 选项不为 ``True`` 则可选项列表最多仅能有一项的 ``selected`` 为 ``True``。

    :param bool multiple: 是否可以多选. 默认单选
    :param value: 下拉选择框初始选中项的值。当 ``multiple=True`` 时， ``value`` 需为list，否则为单个选项的值。
       你也可以通过设置 ``options`` 列表项中的 ``selected`` 字段来设置默认选中选项。
       最终选中项为 ``value`` 参数和 ``options`` 中设置的并集。
    :type value: list or str
    :param bool required: 是否至少选择一项，仅在 ``multiple=True`` 时可用
    :param - label, validate, name, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 如果 ``multiple=True`` 时，返回用户选中的 ``options`` 中的值的列表；否则，返回用户选中的 ``options`` 中的值
    """
    assert options is not None, 'Required `options` parameter in select()'

    item_spec, valid_func = _parse_args(locals(), excludes=['value'])
    item_spec['options'] = _parse_select_options(options)
    if value is not None:
        item_spec['options'] = _set_options_selected(item_spec['options'], value)
    item_spec['type'] = SELECT

    return single_input(item_spec, valid_func, lambda d: d)


def checkbox(label='', options=None, *, inline=None, validate=None, name=None, value=None, help_text=None,
             **other_html_attrs):
    r"""勾选选项。可以多选，也可以不选。

    :param list options: 可选项列表。格式与同 `select()` 函数的 ``options`` 参数
    :param bool inline: 是否将选项显示在一行上。默认每个选项单独占一行
    :param list value: 勾选选项初始选中项。为选项值的列表。
       你也可以通过设置 ``options`` 列表项中的 ``selected`` 字段来设置默认选中选项。
    :param - label, validate, name, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 用户选中的 options 中的值的列表。当用户没有勾选任何选项时，返回空列表
    """
    assert options is not None, 'Required `options` parameter in checkbox()'

    item_spec, valid_func = _parse_args(locals())
    item_spec['options'] = _parse_select_options(options)
    if value is not None:
        del item_spec['value']
        item_spec['options'] = _set_options_selected(item_spec['options'], value)
    item_spec['type'] = CHECKBOX

    return single_input(item_spec, valid_func, lambda d: d)


def radio(label='', options=None, *, inline=None, validate=None, name=None, value=None, required=None,
          help_text=None, **other_html_attrs):
    r"""单选选项

    :param list options: 可选项列表。格式与同 `select()` 函数的 ``options`` 参数
    :param bool inline: 是否将选项显示在一行上。默认每个选项单独占一行
    :param str value: 单选选项初始选中项的值。
       你也可以通过设置 ``options`` 列表项中的 ``selected`` 字段来设置默认选中选项。
    :param bool required: 是否一定要选择一项（默认条件下用户可以不选择任何选项）
    :param - label, validate, name, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: 用户选中的选项的值, 如果用户没有选任何值，返回 ``None``
    """
    assert options is not None, 'Required `options` parameter in radio()'

    item_spec, valid_func = _parse_args(locals())
    item_spec['options'] = _parse_select_options(options)
    if value is not None:
        del item_spec['value']
        item_spec['options'] = _set_options_selected(item_spec['options'], value)
    if required is not None:
        del item_spec['required']
        item_spec['options'][-1]['required'] = required
    item_spec['type'] = RADIO

    return single_input(item_spec, valid_func, lambda d: d)


def _parse_action_buttons(buttons):
    """
    :param label:
    :param actions: action 列表
    action 可用形式：

        * dict: ``{label:选项标签, value:选项值, [type: 按钮类型], [disabled:是否禁止选择]}``
        * tuple or list: ``(label, value, [type], [disabled])``
        * 单值: 此时label和value使用相同的值

    :return: 规格化后的 buttons
    """
    act_res = []
    for act in buttons:
        if isinstance(act, Mapping):
            assert 'label' in act, 'actions item must have label key'
            assert 'value' in act or act.get('type', 'submit') != 'submit' or act.get('disabled'), \
                'actions item must have value key for submit type'
        elif isinstance(act, (list, tuple)):
            assert len(act) in (2, 3, 4), 'actions item format error'
            act = dict(zip(('label', 'value', 'type', 'disabled'), act))
        else:
            act = dict(value=act, label=act)

        act.setdefault('type', 'submit')
        assert act['type'] in ('submit', 'reset', 'cancel'), \
            "submit type muse be 'submit'/'reset'/'cancel', not %r" % act['type']
        act_res.append(act)

    return act_res


def actions(label='', buttons=None, name=None, help_text=None):
    r"""按钮选项。

    在表单上显示为一组按钮，用户点击按钮后依据按钮类型的不同有不同的表现。

    :param list buttons: 按钮列表。列表项的可用形式有：

        * dict: ``{label:按钮标签, value:按钮值, [type: 按钮类型], [disabled:是否禁止选择]}`` .
          若 ``type='reset'/'cancel'`` 或 ``disabled=True`` 可省略 ``value``
        * tuple or list: ``(label, value, [type], [disabled])``
        * 单值: 此时label和value使用相同的值

       其中， ``value`` 可以为任意可JSON序列化的对象。 ``type`` 可选值为:

        * ``'submit'`` : 点击按钮后，立即将整个表单提交，最终表单中本项的值为被点击按钮的 ``value`` 值。 ``'submit'`` 为 ``type`` 的默认值
        * ``'cancel'`` : 取消输入。点击按钮后，立即将整个表单提交，表单值返回 ``None``
        * ``'reset'`` : 点击按钮后，将整个表单重置，输入项将变为初始状态。
          注意：点击 ``type=reset`` 的按钮后，并不会提交表单， ``actions()`` 调用也不会返回

    :param - label, name, help_text: 与 `input` 输入函数的同名参数含义一致
    :return: 若用户点击点击 ``type=submit`` 按钮进行表单提交，返回用户点击的按钮的值；
       若用户点击 ``type=cancel`` 按钮或通过其它方式提交表单，则返回 ``None``

    当 ``actions()`` 作为 `input_group()` 中的最后一个输入项、并且含有 ``type='submit'`` 的按钮时，`input_group()` 表单默认的提交按钮会被当前 ``actions()`` 替换

    **actions使用场景**

    .. _custom_form_ctrl_btn:

    * 实现简单的选择操作:

    .. exportable-codeblock::
        :name: actions-select
        :summary: 使用`actions()`实现简单的选择操作

        confirm = actions('确认删除文件？', ['确认', '取消'], help_text='文件删除后不可恢复')
        if confirm=='确认':  # ..doc-only
            ...  # ..doc-only
        put_markdown('点击了`%s`按钮' % confirm)  # ..demo-only

    相比于其他输入项，使用 `actions()` 用户只需要点击一次就可完成提交。

    * 替换默认的提交按钮:

    .. exportable-codeblock::
        :name: actions-submit
        :summary: 使用`actions()`替换默认的提交按钮

        import json  # ..demo-only
                     # ..demo-only
        info = input_group('Add user', [
            input('username', type=TEXT, name='username', required=True),
            input('password', type=PASSWORD, name='password', required=True),
            actions('actions', [
                {'label': '保存', 'value': 'save'},
                {'label': '保存并添加下一个', 'value': 'save_and_continue'},
                {'label': '重置', 'type': 'reset'},
                {'label': '取消', 'type': 'cancel'},
            ], name='action', help_text='actions'),
        ])
        put_code('info = ' + json.dumps(info, indent=4))
        if info is not None:
            save_user(info['username'], info['password'])  # ..doc-only
            if info['action'] == 'save_and_continue':  # 选择了"保存并添加下一个"
                add_next()  # ..doc-only
                put_text('选择了"保存并添加下一个"')  # ..demo-only

    """
    assert buttons is not None, 'Required `buttons` parameter in actions()'

    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = 'actions'
    item_spec['buttons'] = _parse_action_buttons(buttons)

    return single_input(item_spec, valid_func, lambda d: d)


def _parse_file_size(size):
    if isinstance(size, (int, float)):
        return int(size)
    assert isinstance(size, str), '`size` must be int/float/str, got %s' % type(size)

    size = size.lower()
    for idx, i in enumerate(['k', 'm', 'g'], 1):
        if i in size:
            s = size.replace(i, '')
            base = 2 ** (idx * 10)
            return int(float(s) * base)

    return int(size)


def file_upload(label='', accept=None, name=None, placeholder='Choose file', multiple=False, max_size=0,
                max_total_size=0, required=None, help_text=None, **other_html_attrs):
    r"""文件上传。

    :param accept: 单值或列表, 表示可接受的文件类型。文件类型的可用形式有：

        * 以 ``.`` 字符开始的文件扩展名（例如：``.jpg, .png, .doc``）。
          注意：截至本文档编写之时，微信内置浏览器还不支持这种语法
        * 一个有效的 MIME 类型。
          例如： ``application/pdf`` 、 ``audio/*`` 表示音频文件、``video/*`` 表示视频文件、``image/*`` 表示图片文件。
          参考 https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types

    :type accept: str or list
    :param str placeholder: 未上传文件时，文件上传框内显示的文本
    :param bool multiple: 是否允许多文件上传
    :param int/str max_size: 单个文件的最大大小，超过限制将会禁止上传。默认为0，表示不限制上传文件的大小。

       ``max_size`` 值可以为数字表示的字节数，或以 `K` / `M` / `G` 结尾表示的字符串(分别表示 千字节、兆字节、吉字节，大小写不敏感)。例如:
       ``max_size=500`` , ``max_size='40K'`` , ``max_size='3M'``

    :param int/str max_total_size: 所有文件的最大大小，超过限制将会禁止上传。仅在 ``multiple=True`` 时可用，默认不限制上传文件的大小。 格式同 ``max_size`` 参数
    :param bool required: 是否必须要上传文件。默认为 `False`
    :param - label, name, help_text, other_html_attrs: 与 `input` 输入函数的同名参数含义一致
    :return: ``multiple=False`` 时(默认)，返回dict::

        {
            'filename': 文件名， 
            'content'：文件二进制数据(bytes object), 
            'mime_type': 文件的MIME类型, 
            'last_modified': 文件上次修改时间(时间戳) 
        }
       
       若用户没有上传文件，返回 ``None`` 。

       ``multiple=True`` 时，返回列表，列表项格式同上文 ``multiple=False`` 时的返回值；若用户没有上传文件，返回空列表。

    .. note::
    
        若上传大文件请留意Web框架的文件上传大小限制设置。在使用 :func:`start_server <pywebio.platform.start_server>` 启动PyWebIO应用时，
        可通过 `websocket_max_message_size` 参数设置允许上传的最大文件大小

    """
    item_spec, valid_func = _parse_args(locals())
    item_spec['type'] = 'file'
    item_spec['max_size'] = _parse_file_size(max_size)
    item_spec['max_total_size'] = _parse_file_size(max_total_size)

    def read_file(data):  # data: None or [{'filename':, 'dataurl', 'mime_type', 'last_modified'}, ...]
        for d in data:
            try:
                _, encoded = d['dataurl'].split(",", 1)
            except ValueError:
                encoded = ''
            d['content'] = b64decode(encoded)

        if not multiple:
            return data[0] if len(data) >= 1 else None
        return data

    return single_input(item_spec, valid_func, read_file)


def input_group(label='', inputs=None, validate=None, cancelable=False):
    r"""输入组。向页面上展示一组输入

    :param str label: 输入组标签
    :param list inputs: 输入项列表。列表的内容为对单项输入函数的调用，并在单项输入函数中传入 ``name`` 参数。
    :param callable validate: 输入组校验函数。
        函数签名：``callback(data) -> (name, error_msg)``
        ``validate`` 接收整个表单的值为参数，当校验表单值有效时，返回 ``None`` ，当某项输入值无效时，返回出错输入项的 ``name`` 值和错误提示. 比如:

    .. exportable-codeblock::
        :name: input_group-valid_func
        :summary: `input_group()`输入组校验

        def check_form(data):
            if len(data['name']) > 6:
                return ('name', '名字太长！')
            if data['age'] <= 0:
                return ('age', '年龄不能为负数！')

        data = input_group("Basic info",[
            input('Input your name', name='name'),
            input('Repeat your age', name='age', type=NUMBER)
        ], validate=check_form)

        put_text(data['name'], data['age'])

    :param bool cancelable: 表单是否可以取消。若 ``cancelable=True`` 则会在表单底部显示一个"取消"按钮。
       注意：若 ``inputs`` 中最后一项输入为 `actions()` ，则忽略 ``cancelable``

    :return: 若用户取消表单，返回 ``None`` ,否则返回一个 ``dict`` , 其键为输入项的 ``name`` 值，字典值为输入项的值
    """
    assert inputs is not None, 'Required `inputs` parameter in input_group()'

    spec_inputs = []
    preprocess_funcs = {}
    item_valid_funcs = {}
    for single_input_return in inputs:
        try:
            single_input_return.send(None)  # 协程模式下，带有name参数的单项输入函数通过send(None)来获取协程参数
        except StopIteration as e:
            input_kwargs = e.args[0]
        except AttributeError:
            input_kwargs = single_input_return
        else:
            raise RuntimeError("Can't get kwargs from single input")

        assert all(
            k in (input_kwargs or {})
            for k in ('item_spec', 'preprocess_func', 'valid_func')
        ), "`inputs` value error in `input_group`. Did you forget to add `name` parameter in input function?"

        input_name = input_kwargs['item_spec']['name']
        if input_name in preprocess_funcs:
            raise ValueError("Can't use same `name`:%s in different input in input group!!" % input_name)
        preprocess_funcs[input_name] = input_kwargs['preprocess_func']
        item_valid_funcs[input_name] = input_kwargs['valid_func']
        spec_inputs.append(input_kwargs['item_spec'])

    if all('auto_focus' not in i for i in spec_inputs):  # 每一个输入项都没有设置auto_focus参数
        for i in spec_inputs:
            text_inputs = {TEXT, NUMBER, PASSWORD, SELECT, URL}  # todo update
            if i.get('type') in text_inputs:
                i['auto_focus'] = True
                break

    spec = dict(label=label, inputs=spec_inputs, cancelable=cancelable)
    return input_control(spec, preprocess_funcs=preprocess_funcs, item_valid_funcs=item_valid_funcs,
                         form_valid_funcs=validate)
