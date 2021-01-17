r"""输出内容到用户浏览器

本模块提供了一系列函数来输出不同形式的内容到用户浏览器，并支持灵活的输出控制。

函数清单
--------------
..
  Use https://www.tablesgenerator.com/text_tables to generate/update below table

+-------------+------------------+---------------------------------------------------------+
|             | **函数**         | **简介**                                                |
+-------------+------------------+---------------------------------------------------------+
| 输出域Scope | `set_scope`      | 创建一个新的scope.                                      |
|             +------------------+---------------------------------------------------------+
|             | `get_scope`      | 获取当前运行时scope栈中的scope名                        |
|             +------------------+---------------------------------------------------------+
|             | `clear`          | 清空scope内容                                           |
|             +------------------+---------------------------------------------------------+
|             | `remove`         | 移除Scope                                               |
|             +------------------+---------------------------------------------------------+
|             | `scroll_to`      | 将页面滚动到 scope Scope处                              |
|             +------------------+---------------------------------------------------------+
|             | `use_scope`      | 开启/进入输出域                                         |
+-------------+------------------+---------------------------------------------------------+
| 内容输出    | `put_text`       | 输出文本                                                |
|             +------------------+---------------------------------------------------------+
|             | `put_markdown`   | 输出Markdown                                            |
|             +------------------+---------------------------------------------------------+
|             | `put_html`       | 输出Html                                                |
|             +------------------+---------------------------------------------------------+
|             | `put_link`       | 输出链接                                                |
|             +------------------+---------------------------------------------------------+
|             | `put_processbar` | 输出进度条                                              |
|             +------------------+---------------------------------------------------------+
|             | `set_processbar` | 设置进度条进度                                          |
|             +------------------+---------------------------------------------------------+
|             | `put_loading`    | 输出加载提示                                            |
|             +------------------+---------------------------------------------------------+
|             | `put_code`       | 输出代码块                                              |
|             +------------------+---------------------------------------------------------+
|             | `put_table`      | 输出表格                                                |
|             +------------------+---------------------------------------------------------+
|             | `put_buttons`    | 输出一组按钮，并绑定点击事件                            |
|             +------------------+---------------------------------------------------------+
|             | `put_image`      | 输出图片                                                |
|             +------------------+---------------------------------------------------------+
|             | `put_file`       | 显示一个文件下载链接                                    |
|             +------------------+---------------------------------------------------------+
|             | `put_collapse`   | 输出可折叠的内容                                        |
|             +------------------+---------------------------------------------------------+
|             | `put_scrollable` | 固定高度内容输出区域，内容超出则显示滚动条              |
|             +------------------+---------------------------------------------------------+
|             | `put_widget`     | 输出自定义的控件                                        |
+-------------+------------------+---------------------------------------------------------+
| 其他交互    | `toast`          | 显示一条通知消息                                        |
|             +------------------+---------------------------------------------------------+
|             | `popup`          | 显示弹窗                                                |
|             +------------------+---------------------------------------------------------+
|             | `close_popup`    | 关闭正在显示的弹窗                                      |
+-------------+------------------+---------------------------------------------------------+
| 布局与样式  | `put_row`        | 使用行布局输出内容                                      |
|             +------------------+---------------------------------------------------------+
|             | `put_column`     | 使用列布局输出内容                                      |
|             +------------------+---------------------------------------------------------+
|             | `put_grid`       | 使用网格布局输出内容                                    |
|             +------------------+---------------------------------------------------------+
|             | `span`           | 在 `put_table()` 和 `put_grid()` 中设置内容跨单元格     |
|             +------------------+---------------------------------------------------------+
|             | `style`          | 自定义输出内容的css样式                                 |
+-------------+------------------+---------------------------------------------------------+
| 其他        | `output`         | 内容占位符                                              |
+-------------+------------------+---------------------------------------------------------+


输出域Scope
--------------
.. autofunction:: set_scope
.. autofunction:: get_scope
.. autofunction:: clear
.. autofunction:: remove
.. autofunction:: scroll_to
.. autofunction:: use_scope

内容输出
--------------
.. autofunction:: put_text
.. autofunction:: put_markdown
.. autofunction:: put_html
.. autofunction:: put_link
.. autofunction:: put_processbar
.. autofunction:: set_processbar
.. autofunction:: put_loading
.. autofunction:: put_code
.. autofunction:: put_table
.. autofunction:: span
.. autofunction:: put_buttons
.. autofunction:: put_image
.. autofunction:: put_file
.. autofunction:: put_collapse
.. autofunction:: put_scrollable
.. autofunction:: put_widget

其他交互
--------------
.. autofunction:: toast
.. autofunction:: popup
.. autofunction:: close_popup

.. _style_and_layout:

布局与样式
--------------
.. autofunction:: put_row
.. autofunction:: put_column
.. autofunction:: put_grid
.. autofunction:: style

其他
--------------
.. autofunction::  output

"""
import io
import logging
import string
from base64 import b64encode
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Union

from .io_ctrl import output_register_callback, send_msg, Output, safely_destruct_output_when_exp, OutputList
from .session import get_current_session, download
from .utils import random_str, iscoroutinefunction, is_html_safe_value

try:
    from PIL.Image import Image as PILImage
except ImportError:
    PILImage = type('MockPILImage', (), dict(__init__=None))

logger = logging.getLogger(__name__)

__all__ = ['Position', 'remove', 'scroll_to',
           'put_text', 'put_html', 'put_code', 'put_markdown', 'use_scope', 'set_scope', 'clear', 'remove',
           'put_table', 'put_buttons', 'put_image', 'put_file', 'PopupSize', 'popup',
           'close_popup', 'put_widget', 'put_collapse', 'put_link', 'put_scrollable', 'style', 'put_column',
           'put_row', 'put_grid', 'column', 'row', 'grid', 'span', 'put_processbar', 'set_processbar', 'put_loading',
           'output', 'toast', 'get_scope']


# popup尺寸
class PopupSize:
    LARGE = 'large'
    NORMAL = 'normal'
    SMALL = 'small'


class Position:
    TOP = 'top'
    MIDDLE = 'middle'
    BOTTOM = 'bottom'


# put_xxx()中的position值
class OutputPosition:
    TOP = 0
    BOTTOM = -1


class Scope:
    Current = -1
    Root = 0
    Parent = -2


_scope_name_allowed_chars = set(string.ascii_letters + string.digits + '_-')


def _parse_scope(name, no_css_selector=False):
    """获取实际用于前端html页面中的CSS选择器/元素名

    name 为str/tuple，为str时，视作Dom ID名； tuple格式为(css选择器符号, 元素名)，仅供内部实现使用
    """
    selector = '#'
    if isinstance(name, tuple):
        selector, name = name

    name = name.replace(' ', '-')

    if no_css_selector:
        selector = ''

    return '%spywebio-scope-%s' % (selector, name)


def set_scope(name, container_scope=Scope.Current, position=OutputPosition.BOTTOM, if_exist=None):
    """创建一个新的scope.

    :param str name: scope名
    :param int/str container_scope: 此scope的父scope. 可以直接指定父scope名或使用 `Scope` 常量. scope不存在时，不进行任何操作.
    :param int position: 在父scope中创建此scope的位置.
       `OutputPosition.TOP` : 在父scope的顶部创建, `OutputPosition.BOTTOM` : 在父scope的尾部创建
    :param str if_exist: 已经存在 ``name`` scope 时如何操作:

        - `None` 表示不进行任何操作
        - `'remove'` 表示先移除旧scope再创建新scope
        - `'clear'` 表示将旧scope的内容清除，不创建新scope

       默认为 `None`
    """
    if isinstance(container_scope, int):
        container_scope = get_current_session().get_scope_name(container_scope)

    assert is_html_safe_value(name), "Scope name only allow letter/digit/'_'/'-' char."
    send_msg('output_ctl', dict(set_scope=_parse_scope(name, no_css_selector=True),
                                container=_parse_scope(container_scope),
                                position=position, if_exist=if_exist))


def get_scope(stack_idx=Scope.Current):
    """获取当前运行时scope栈中的scope名

    :param int stack_idx: 需要获取的scope在scope栈中的索引值。默认返回当前scope名

        -1表示当前scope，-2表示进入当前scope前的scope，依次类推；0表示 `ROOT` scope
    :return: 返回Scope栈中对应索引的scope名，索引错误时返回None
    """
    try:
        return get_current_session().get_scope_name(stack_idx)
    except IndexError:
        return None


def clear(scope=Scope.Current):
    """清空scope内容

    :param int/str scope: 可以直接指定scope名或使用 `Scope` 常量
    """
    if isinstance(scope, int):
        scope = get_current_session().get_scope_name(scope)
    send_msg('output_ctl', dict(clear=_parse_scope(scope)))


def remove(scope=Scope.Current):
    """移除Scope"""
    if isinstance(scope, int):
        scope = get_current_session().get_scope_name(scope)
    assert scope != 'ROOT', "Can not remove `ROOT` scope."
    send_msg('output_ctl', dict(remove=_parse_scope(scope)))


def scroll_to(scope=Scope.Current, position=Position.TOP):
    """scroll_to(scope, position=Position.TOP)

    将页面滚动到 ``scope`` Scope处

    :param str/int scope: Scope名
    :param str position: 将Scope置于屏幕可视区域的位置。可用值：

       * ``Position.TOP`` : 滚动页面，让Scope位于屏幕可视区域顶部
       * ``Position.MIDDLE`` : 滚动页面，让Scope位于屏幕可视区域中间
       * ``Position.BOTTOM`` : 滚动页面，让Scope位于屏幕可视区域底部
    """
    if isinstance(scope, int):
        scope = get_current_session().get_scope_name(scope)
    send_msg('output_ctl', dict(scroll_to=_parse_scope(scope), position=position))


def _get_output_spec(type, scope, position, **other_spec):
    """
    获取输出类指令的spec字段

    :param str type: 输出类型
    :param int/str scope: 输出到的scope
    :param int position: 在scope输出的位置， `OutputPosition.TOP` : 输出到scope的顶部， `OutputPosition.BOTTOM` : 输出到scope的尾部
    :param other_spec: 额外的输出参数，值为None的参数不会包含到返回值中

    :return dict:  ``output`` 指令的spec字段
    """
    spec = dict(type=type)

    # 将非None的参数加入SPEC中
    spec.update({k: v for k, v in other_spec.items() if v is not None})

    if isinstance(scope, int):
        scope_name = get_current_session().get_scope_name(scope)
    else:
        scope_name = scope

    spec['scope'] = _parse_scope(scope_name)
    spec['position'] = position

    return spec


def put_text(*texts, sep=' ', inline=False, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """
    输出文本内容

    :param texts: 要输出的内容。类型可以为任意对象，对非字符串对象会应用 `str()` 函数作为输出值。
    :param str sep: 输出分隔符
    :param bool inline: 文本行末不换行。默认换行
    :param int/str scope: 内容输出的目标scope，若scope不存在，则不进行任何输出操作。

       可以直接指定目标Scope名，或者使用int通过索引Scope栈来确定Scope：0表示最顶层也就是ROOT Scope，-1表示当前Scope，-2表示进入当前Scope的前一个Scope，...
    :param int position: 在scope中输出的位置。

       position>=0时表示输出到scope的第position个(从0计数)子元素的前面；position<0时表示输出到scope的倒数第position个(从-1计数)元素之后。

    参数 `scope` 和 `position` 的更多使用说明参见 :ref:`用户手册 <scope_param>`
    """
    content = sep.join(str(i) for i in texts)
    spec = _get_output_spec('text', content=content, inline=inline, scope=scope, position=position)
    return Output(spec)


def put_html(html, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """
    输出Html内容。

    与支持通过Html输出内容到 `Jupyter Notebook <https://nbviewer.jupyter.org/github/ipython/ipython/blob/master/examples/IPython%20Kernel/Rich%20Output.ipynb#HTML>`_ 的库兼容。

    :param html: html字符串或实现了 `IPython.display.HTML` 接口的类的实例
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    if hasattr(html, '__html__'):
        html = html.__html__()

    spec = _get_output_spec('html', content=html, scope=scope, position=position)
    return Output(spec)


def put_code(content, language='', scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """
    输出代码块

    :param str content: 代码内容
    :param str language: 代码语言
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    code = "```%s\n%s\n```" % (language, content)
    return put_markdown(code, scope=scope, position=position)


def put_markdown(mdcontent, strip_indent=0, lstrip=False, scope=Scope.Current,
                 position=OutputPosition.BOTTOM) -> Output:
    """
    输出Markdown内容。

    :param str mdcontent: Markdown文本
    :param int strip_indent: 对于每一行，若前 ``strip_indent`` 个字符都为空格，则将其去除
    :param bool lstrip: 是否去除每一行开始的空白符
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    当在函数中使用Python的三引号语法输出多行内容时，为了排版美观可能会对Markdown文本进行缩进，
    这时候，可以设置 ``strip_indent`` 或 ``lstrip`` 来防止Markdown错误解析(但不要同时使用 ``strip_indent`` 和 ``lstrip`` )::

        # 不使用strip_indent或lstrip
        def hello():
            put_markdown(r\""" # H1
        This is content.
        \""")

        # 使用lstrip
        def hello():
            put_markdown(r\""" # H1
            This is content.
            \""", lstrip=True)

        # 使用strip_indent
        def hello():
            put_markdown(r\""" # H1
            This is content.
            \""", strip_indent=4)
    """
    if strip_indent:
        lines = (
            i[strip_indent:] if (i[:strip_indent] == ' ' * strip_indent) else i
            for i in mdcontent.splitlines()
        )
        mdcontent = '\n'.join(lines)
    if lstrip:
        lines = (i.lstrip() for i in mdcontent.splitlines())
        mdcontent = '\n'.join(lines)

    spec = _get_output_spec('markdown', content=mdcontent, scope=scope, position=position)
    return Output(spec)


class span_:
    def __init__(self, content, row=1, col=1):
        self.content, self.row, self.col = content, row, col


@safely_destruct_output_when_exp('content')
def span(content, row=1, col=1):
    """用于在 :func:`put_table()` 和 :func:`put_grid()` 中设置内容跨单元格

    :param content: 单元格内容
    :param int row: 竖直方向跨度, 即：跨行的数目
    :param int col: 水平方向跨度, 即：跨列的数目

    :Example:

    .. exportable-codeblock::
        :name: span
        :summary: 使用`span()`合并单元格

        put_table([
            ['C'],
            [span('E', col=2)],  # 'E' 跨2列
        ], header=[span('A', row=2), 'B'])  # 'A' 跨2行

        put_grid([
            [put_text('A'), put_text('B')],
            [span(put_text('A'), col=2)],  # 'A' 跨2列
        ])

    """
    return span_(content, row, col)


@safely_destruct_output_when_exp('tdata')
def put_table(tdata, header=None, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """
    输出表格

    :param list tdata: 表格数据。列表项可以为 ``list`` 或者 ``dict`` , 单元格的内容可以为字符串或 ``put_xxx`` 类型的输出函数。
       数组项可以使用 :func:`span()` 函数来设定单元格跨度。
    :param list header: 设定表头。
       当 ``tdata`` 的列表项为 ``list`` 类型时，若省略 ``header`` 参数，则使用 ``tdata`` 的第一项作为表头。表头项可以使用 :func:`span()` 函数来设定单元格跨度。

       当 ``tdata`` 为字典列表时，使用 ``header`` 指定表头顺序，不可省略。
       此时， ``header`` 格式可以为 <字典键>列表 或者 ``(<显示文本>, <字典键>)`` 列表。

    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    使用示例:

    .. exportable-codeblock::
        :name: put_table
        :summary: 使用`put_table()`输出表格

        # 'Name'单元格跨2行、'Address'单元格跨2列
        put_table([
            [span('Name',row=2), span('Address', col=2)],
            ['City', 'Country'],
            ['Wang', 'Beijing', 'China'],
            ['Liu', 'New York', 'America'],
        ])
        ## ----

        # 单元格为 ``put_xxx`` 类型的输出函数
        put_table([
            ['Type', 'Content'],
            ['html', put_html('X<sup>2</sup>')],
            ['text', '<hr/>'],
            ['buttons', put_buttons(['A', 'B'], onclick=...)],  # ..doc-only
            ['buttons', put_buttons(['A', 'B'], onclick=ut_text)],  # ..demo-only
            ['markdown', put_markdown('`Awesome PyWebIO!`')],
            ['file', put_file('hello.text', b'')],
            ['table', put_table([['A', 'B'], ['C', 'D']])]
        ])
        ## ----

        # 设置表头
        put_table([
            ['Wang', 'M', 'China'],
            ['Liu', 'W', 'America'],
        ], header=['Name', 'Gender', 'Address'])
        ## ----

        # dict类型的表格行
        put_table([
            {"Course":"OS", "Score": "80"},
            {"Course":"DB", "Score": "93"},
        ], header=["Course", "Score"])  # or header=[("课程", "Course"), ("得分" ,"Score")]

    .. versionadded:: 0.3
       单元格的内容支持 ``put_xxx`` 类型的输出函数
    """

    # Change ``dict`` row table to list row table
    if tdata and isinstance(tdata[0], dict):
        if isinstance(header[0], (list, tuple)):
            header_ = [h[0] for h in header]
            order = [h[-1] for h in header]
        else:
            header_ = order = header

        tdata = [
            [row.get(k, '') for k in order]
            for row in tdata
        ]
        header = header_
    else:
        tdata = [list(i) for i in tdata]  # copy data

    if header:
        tdata = [header, *tdata]

    span = {}
    for x in range(len(tdata)):
        for y in range(len(tdata[x])):
            cell = tdata[x][y]
            if isinstance(cell, span_):
                tdata[x][y] = cell.content
                span['%s,%s' % (x, y)] = dict(col=cell.col, row=cell.row)
            elif not isinstance(cell, Output):
                tdata[x][y] = str(cell)

    spec = _get_output_spec('table', data=tdata, span=span, scope=scope, position=position)
    return Output(spec)


def _format_button(buttons):
    """
    格式化按钮参数
    :param buttons: button列表， button可用形式：
        {label:, value:, }
        (label, value, )
        value 单值，label等于value

    :return: [{value:, label:, }, ...]
    """

    btns = []
    for btn in buttons:
        if isinstance(btn, Mapping):
            assert 'value' in btn and 'label' in btn, 'actions item must have value and label key'
        elif isinstance(btn, (list, tuple)):
            assert len(btn) == 2, 'actions item format error'
            btn = dict(zip(('label', 'value'), btn))
        else:
            btn = dict(value=btn, label=btn)
        btns.append(btn)
    return btns


def put_buttons(buttons, onclick, small=None, link_style=False, scope=Scope.Current, position=OutputPosition.BOTTOM,
                **callback_options) -> Output:
    """
    输出一组按钮，并绑定点击事件

    :param list buttons: 按钮列表。列表项的可用形式有：

        * dict: ``{label:选项标签, value:选项值}``
        * tuple or list: ``(label, value)``
        * 单值: 此时label和value使用相同的值

        其中， ``value`` 可以为任意可json序列化的对象。使用dict类型的列表项时，支持使用 ``color`` key设置按钮颜色，可选值为 `primary` 、
        `secondary` 、 `success` 、 `danger` 、 `warning` 、 `info` 、 `light` 、 `dark`

        例如:

        .. exportable-codeblock::
            :name: put_buttons-btn_class
            :summary: `put_buttons()`按钮样式

            put_buttons([dict(label='primary', value='p', color='primary')], onclick=...)  # ..doc-only
            put_buttons([  # ..demo-only
                dict(label=i, value=i, color=i)  # ..demo-only
                for i in ['primary' , 'secondary' , 'success' , 'danger' , 'warning' , 'info' , 'light' , 'dark']  # ..demo-only
            ], onclick=put_text)  # ..demo-only

    :type onclick: Callable / list
    :param onclick: 按钮点击回调函数. ``onclick`` 可以是函数或者函数组成的列表.

       ``onclick`` 为函数时， 签名为 ``onclick(btn_value)``. ``btn_value`` 为被点击的按钮的 ``value`` 值

       ``onclick`` 为列表时，列表内函数的签名为 ``func()``. 此时，回调函数与 ``buttons`` 一一对应

       Tip: 可以使用 ``functools.partial`` 来在 ``onclick`` 中保存更多上下文信息.

       Note: 当使用 :ref:`基于协程的会话实现 <coroutine_based_session>` 时，回调函数可以为协程函数.
    :param bool small: 是否显示小号按钮，默认为False
    :param bool link_style: 是否将按钮显示为链接样式，默认为False
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    :param callback_options: 回调函数的其他参数。根据选用的 session 实现有不同参数

       CoroutineBasedSession 实现
           * mutex_mode: 互斥模式。默认为 ``False`` 。若为 ``True`` ，则在运行回调函数过程中，无法响应当前按钮组的新点击事件，仅当 ``onclick`` 为协程函数时有效

       ThreadBasedSession 实现
           * serial_mode: 串行模式模式。默认为 ``False`` ，此时每次触发回调，回调函数会在新线程中立即执行。
           对于开启了serial_mode的回调，都会在会话内的一个固定线程内执行，当会话运行此回调时，其他所有新的点击事件的回调(包括 ``serial_mode=False`` 的回调)都将排队等待当前点击事件运行完成。
           如果回调函数运行时间很短，可以开启 ``serial_mode`` 来提高性能。

    使用示例:

    .. exportable-codeblock::
        :name: put_buttons
        :summary: 使用`put_buttons()`输出按钮

        from functools import partial

        def row_action(choice, id):
            put_text("You click %s button with id: %s" % (choice, id))

        put_buttons(['edit', 'delete'], onclick=partial(row_action, id=1))
        ## ----

        def edit():
            put_text("You click edit button")
        def delete():
            put_text("You click delete button")

        put_buttons(['edit', 'delete'], onclick=[edit, delete])
    """
    btns = _format_button(buttons)

    if isinstance(onclick, Sequence):
        assert len(btns) == len(onclick), "`onclick` and `buttons` must be same length."
        onclick = {btn['value']: callback for btn, callback in zip(btns, onclick)}

    def click_callback(btn_val):
        if isinstance(onclick, dict):
            func = onclick.get(btn_val, lambda: None)
            return func()
        else:
            return onclick(btn_val)

    callback_id = output_register_callback(click_callback, **callback_options)
    spec = _get_output_spec('buttons', callback_id=callback_id, buttons=btns, small=small,
                            scope=scope, position=position, link=link_style)

    return Output(spec)


def put_image(src, format=None, title='', width=None, height=None,
              scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """输出图片。

    :param src: 图片内容. 类型可以为字符串类型的URL或者是 bytes-like object 或者为 ``PIL.Image.Image`` 实例
    :param str title: 图片描述
    :param str width: 图像的宽度，可以是CSS像素(数字px)或者百分比(数字%)。
    :param str height: 图像的高度，可以是CSS像素(数字px)或者百分比(数字%)。可以只指定 width 和 height 中的一个值，浏览器会根据原始图像进行缩放。
    :param str format: 图片格式。如 ``png`` , ``jpeg`` , ``gif`` 等, 仅在 `src` 为非URL时有效
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    if isinstance(src, PILImage):
        format = src.format
        imgByteArr = io.BytesIO()
        src.save(imgByteArr, format=format)
        src = imgByteArr.getvalue()

    if isinstance(src, (bytes, bytearray)):
        b64content = b64encode(src).decode('ascii')
        format = '' if format is None else ('image/%s' % format)
        src = "data:{format};base64, {b64content}".format(format=format, b64content=b64content)

    width = 'width="%s"' % width if width is not None else ''
    height = 'height="%s"' % height if height is not None else ''

    html = r'<img src="{src}" alt="{title}" {width} {height}/>'.format(src=src, title=title, height=height, width=width)
    return put_html(html, scope=scope, position=position)


def put_file(name, content, label=None, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """显示一个文件下载链接。
    在浏览器上的显示为一个以文件名为名的链接，点击链接后浏览器自动下载文件。

    :param str name: 下载保存为的文件名
    :param content: 文件内容. 类型为 bytes-like object
    :param str label: 下载链接的显示文本，默认和文件名相同
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    if label is None:
        label = name
    output = put_buttons(buttons=[label], link_style=True,
                         onclick=[lambda: download(name, content)],
                         scope=scope, position=position)
    return output


def put_link(name, url=None, app=None, new_window=False, scope=Scope.Current,
             position=OutputPosition.BOTTOM) -> Output:
    """输出链接到其他页面或PyWebIO App的超链接

    :param str name: 链接名称
    :param str url: 链接到的页面地址
    :param str app: 链接到的PyWebIO应用名
    :param bool new_window: 是否在新窗口打开链接
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    ``url`` 和 ``app`` 参数必须指定一个但不可以同时指定
    """
    assert bool(url is None) != bool(app is None), "Must set `url` or `app` parameter but not both"

    href = 'javascript:WebIO.openApp(%r, %d)' % (app, new_window) if app is not None else url
    target = '_blank' if (new_window and url) else '_self'
    html = '<a href="{href}" target="{target}">{name}</a>'.format(href=href, target=target, name=name)
    return put_html(html, scope=scope, position=position)


def put_processbar(name, init=0, label=None, auto_close=False, scope=Scope.Current,
                   position=OutputPosition.BOTTOM) -> Output:
    """输出进度条

    :param str name: 进度条名称，为进度条的唯一标识
    :param float init: 进度条初始值. 进度条的值在 0 ~ 1 之间
    :param str label: 进度条显示的标签. 默认为当前进度的百分比
    :param bool auto_close: 是否在进度完成后关闭进度条
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    processbar_id = 'webio-processbar-%s' % name
    percentage = init * 100
    label = '%.1f%%' % percentage if label is None else label
    tpl = """<div class="progress" style="margin-top: 4px;">
                <div id={{elem_id}} class="progress-bar bg-info progress-bar-striped progress-bar-animated" role="progressbar"
                     style="width: {{percentage}}%;" aria-valuenow="{{init}}" aria-valuemin="0" aria-valuemax="1" data-auto-close="{{auto_close}}">{{label}}
                </div>
            </div>"""
    return put_widget(tpl, data=dict(elem_id=processbar_id, init=init, label=label,
                                     percentage=percentage, auto_close=int(bool(auto_close))), scope=scope,
                      position=position)


def set_processbar(name, value, label=None):
    """设置进度条进度

    :param str name: 进度条名称
    :param float value: 进度条的值. 范围在 0 ~ 1 之间
    :param str label: 进度条显示的标签. 默认为当前进度的百分比
    """
    from pywebio.session import run_js

    processbar_id = 'webio-processbar-%s' % name
    percentage = value * 100
    label = '%.1f%%' % percentage if label is None else label

    js_code = """
    let bar = $("#{processbar_id}");
    bar[0].style.width = "{percentage}%";
    bar.attr("aria-valuenow", "{value}");
    bar.text({label!r});
    """.format(processbar_id=processbar_id, percentage=percentage, value=value, label=label)
    if value == 1:
        js_code += "if(bar.data('autoClose')=='1')bar.parent().remove();"

    run_js(js_code)


def put_loading(shape='border', color='dark', scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """显示一个加载提示

    :param str shape: 加载提示的形状, 可选值: `'border'` (默认，旋转的圆环)、 `'grow'` (大小渐变的圆点)

    :param str color: 加载提示的颜色, 可选值: `'primary'` 、 `'secondary'` 、 `'success'` 、 `'danger'` 、
     `'warning'` 、`'info'`  、`'light'`  、 `'dark'` (默认)
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    .. note::
        可以通过 :func:`style()` 设置加载提示的尺寸:

        .. exportable-codeblock::
            :name: put_loading-size
            :summary: `put_loading()`自定义加载提示尺寸

            put_loading()  # ..demo-only
            style(put_loading(), 'width:4rem; height:4rem')
    """
    assert shape in ('border', 'grow'), "shape must in ('border', 'grow')"
    assert color in {'primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark'}

    html = """<div class="spinner-{shape} text-{color}" role="status">
                <span class="sr-only">Loading...</span>
            </div>""".format(shape=shape, color=color)
    return put_html(html, scope=scope, position=position)


@safely_destruct_output_when_exp('content')
def put_collapse(title, content, open=False, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """输出可折叠的内容

    :param str title: 内容标题
    :type content: list/str/put_xxx()
    :param content: 内容可以为字符串或 ``put_xxx`` 类输出函数的返回值，或者由它们组成的列表。
    :param bool open: 是否默认展开折叠内容。默认不展开内容
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    if not isinstance(content, (list, tuple, OutputList)):
        content = [content]

    for item in content:
        assert isinstance(item, (str, Output)), "put_collapse() content must be list of str/put_xxx()"

    tpl = """<details {{#open}}open{{/open}}>
        <summary>{{title}}</summary>
        {{#contents}}
            {{& pywebio_output_parse}}
        {{/contents}}
    </details>"""
    return put_widget(tpl, dict(title=title, contents=content, open=open), scope=scope, position=position)


@safely_destruct_output_when_exp('content')
def put_scrollable(content, max_height=400, horizon_scroll=False, border=True, scope=Scope.Current,
                   position=OutputPosition.BOTTOM) -> Output:
    """固定高度内容输出区域，内容超出则显示滚动条

    :type content: list/str/put_xxx()
    :param content: 内容可以为字符串或 ``put_xxx`` 类输出函数的返回值，或者由它们组成的列表。
    :param int max_height: 区域的最大高度（像素），内容超出次高度则使用滚动条
    :param bool horizon_scroll: 是否显示水平滚动条
    :param bool border: 是否显示边框
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    if not isinstance(content, (list, tuple, OutputList)):
        content = [content]

    for item in content:
        assert isinstance(item, (str, Output)), "put_collapse() content must be list of str/put_xxx()"

    tpl = """<div style="max-height: {{max_height}}px;
            overflow-y: scroll;
            {{#horizon_scroll}}overflow-x: scroll;{{/horizon_scroll}}
            {{#border}} 
            border: 1px solid rgba(0,0,0,.125);
            box-shadow: inset 0 0 2px 0 rgba(0,0,0,.1); 
            {{/border}}
            padding: 10px;
            margin-bottom: 10px;">

        {{#contents}}
            {{& pywebio_output_parse}}
        {{/contents}}
    </div>"""
    return put_widget(template=tpl,
                      data=dict(contents=content, max_height=max_height, horizon_scroll=horizon_scroll, border=border),
                      scope=scope, position=position)


@safely_destruct_output_when_exp('data')
def put_widget(template, data, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """输出自定义的控件

    :param template: html模版，使用 `mustache.js <https://github.com/janl/mustache.js>`_ 语法
    :param dict data:  渲染模版使用的数据.

       数据可以包含输出函数( ``put_xxx()`` )的返回值, 可以使用 ``pywebio_output_parse`` 函数来解析 ``put_xxx()`` 内容；对于字符串输入， ``pywebio_output_parse`` 会将解析成文本.

       ⚠️：使用 ``pywebio_output_parse`` 函数时，需要关闭mustache的html转义: ``{{& pywebio_output_parse}}`` , 参见下文示例.
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    :Example:

    .. exportable-codeblock::
        :name: put_widget
        :summary: 使用`put_widget()`输出自定义的控件

        tpl = '''
        <details>
            <summary>{{title}}</summary>
            {{#contents}}
                {{& pywebio_output_parse}}
            {{/contents}}
        </details>
        '''

        put_widget(tpl, {
            "title": 'More content',
            "contents": [
                'text',
                put_markdown('~~删除线~~'),
                put_table([
                    ['商品', '价格'],
                    ['苹果', '5.5'],
                    ['香蕉', '7'],
                ])
            ]
        })
    """
    spec = _get_output_spec('custom_widget', template=template, data=data, scope=scope, position=position)
    return Output(spec)


@safely_destruct_output_when_exp('content')
def put_row(content, size=None, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """使用行布局输出内容. 内容在水平方向从左往右排列成一行

    :param list content: 子元素列表, 列表项为 ``put_xxx()`` 调用或者 ``None`` , ``None`` 表示空白列间距
    :param str size:
       | 用于指示子元素的宽度, 为空格分割的宽度值列表.
       | 宽度值需要和 ``content`` 中子元素一一对应( ``None`` 子元素也要对应宽度值).
       | size 默认给 ``None`` 元素分配10像素宽度，将剩余元素平均分配宽度.

       宽度值可用格式:

        - 像素值: 例如: ``100px``
        - 百分比: 表示占可用宽度的百分比. 例如: ``33.33%``
        - ``fr`` 关键字: 表示比例关系, 2fr 表示的宽度为 1fr 的两倍
        - ``auto`` 关键字: 表示由浏览器自己决定长度
        - ``minmax(min, max)`` : 产生一个长度范围，表示长度就在这个范围之中。它接受两个参数，分别为最小值和最大值。
          例如: ``minmax(100px, 1fr)`` 表示长度不小于100px，不大于1fr

    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    :Example:

    .. exportable-codeblock::
        :name: put_row
        :summary: 使用`put_row()`进行行布局

        put_row([put_code('A'), None, put_code('B')])  # 左右两个等宽度的代码块，中间间隔10像素
        ## ----

        put_row([put_code('A'), None, put_code('B')], size='40% 10px 60%')  # 左右两代码块宽度比2:3, 和size='2fr 10px 3fr'等价

    """
    return _row_column_layout(content, flow='column', size=size, scope=scope, position=position)


@safely_destruct_output_when_exp('content')
def put_column(content, size=None, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """使用列布局输出内容. 内容在竖直方向从上往下排列成一列

    :param list content: 子元素列表, 列表项为 ``put_xxx()`` 调用或者 ``None`` , ``None`` 表示空白行间距
    :param str size: 用于指示子元素的高度, 为空格分割的高度值列表. 可用格式参考 `put_row()` 函数的 ``size`` 参数注释.
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """

    return _row_column_layout(content, flow='row', size=size, scope=scope, position=position)


def _row_column_layout(content, flow, size, scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    if not isinstance(content, (list, tuple, OutputList)):
        content = [content]

    if not size:
        size = ' '.join('1fr' if c is not None else '10px' for c in content)

    content = [c if c is not None else put_html('<div></div>') for c in content]
    for item in content:
        assert isinstance(item, Output), "put_row() content must be list of put_xxx()"

    style = 'grid-auto-flow: {flow}; grid-template-{flow}s: {size};'.format(flow=flow, size=size)
    tpl = """
    <div style="display: grid; %s">
        {{#contents}}
            {{& pywebio_output_parse}}
        {{/contents}}
    </div>""".strip() % style
    return put_widget(template=tpl, data=dict(contents=content), scope=scope,
                      position=position)


@safely_destruct_output_when_exp('content')
def put_grid(content, cell_width='auto', cell_height='auto', cell_widths=None, cell_heights=None, direction='row',
             scope=Scope.Current, position=OutputPosition.BOTTOM) -> Output:
    """使用网格布局输出内容

    :param content: 输出内容. ``put_xxx()`` / None 组成的二维数组, None 表示空白. 数组项可以使用 :func:`span()` 函数设置元素在网格的跨度.
    :param str cell_width: 网格元素的宽度. 宽度值格式参考 `put_row()` 函数的 ``size`` 参数注释.
    :param str cell_height: 网格元素的高度. 高度值格式参考 `put_row()` 函数的 ``size`` 参数注释.
    :param str cell_widths: 网格每一列的宽度. 宽度值用空格分隔. 不可以和 `cell_width` 参数同时使用. 宽度值格式参考 `put_row()` 函数的 ``size`` 参数注释.
    :param str cell_heights: 网格每一行的高度. 高度值用空格分隔. 不可以和 `cell_height` 参数同时使用. 高度值格式参考 `put_row()` 函数的 ``size`` 参数注释.
    :param str direction: 排列方向. 为 ``'row'`` 或 ``'column'`` .

        | ``'row'`` 时表示，content中的每一个子数组代表网格的一行;
        | ``'column'`` 时表示，content中的每一个子数组代表网格的一列.

    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    :Example:

    .. exportable-codeblock::
        :name: put_grid
        :summary: 使用`put_grid()`进行网格布局

        put_grid([
            [put_text('A'), put_text('B'), put_text('C')],
            [None, span(put_text('D'), col=2, row=1)],
            [put_text('E'), put_text('F'), put_text('G')],
        ], cell_width='100px', cell_height='100px')
    """
    assert direction in ('row', 'column'), '"direction" parameter must be "row" or "column"'

    lens = [0] * len(content)
    for x in range(len(content)):
        for y in range(len(content[x])):
            cell = content[x][y]
            if isinstance(cell, span_):
                for i in range(cell.row): lens[x + i] += cell.col

                css = 'grid-row-start: span {row}; grid-column-start: span {col};'.format(row=cell.row, col=cell.col)
                elem = put_html('<div></div>') if cell.content is None else cell.content
                content[x][y] = style(elem, css)
            else:
                lens[x] += 1

            if content[x][y] is None:
                content[x][y] = put_html('<div></div>')

    # 为长度不足的行添加空元素
    m = max(lens)
    for idx, i in enumerate(content):
        i.extend(put_html('<div></div>') for _ in range(m - lens[idx]))

    row_cnt, col_cnt = len(content), m
    if direction == 'column':
        row_cnt, col_cnt = m, len(content)

    if not cell_widths:
        cell_widths = 'repeat({col_cnt},{cell_width})'.format(col_cnt=col_cnt, cell_width=cell_width)
    if not cell_heights:
        cell_heights = 'repeat({row_cnt},{cell_height})'.format(row_cnt=row_cnt, cell_height=cell_height)

    css = ('grid-auto-flow: {flow};'
           'grid-template-columns: {cell_widths};'
           'grid-template-rows: {cell_heights};'
           ).format(flow=direction, cell_heights=cell_heights, cell_widths=cell_widths)

    tpl = """
    <div style="display: grid; %s">
        {{#contents}}
            {{#.}}
                {{& pywebio_output_parse}}
            {{/.}}
        {{/contents}}
    </div>""".strip() % css
    return put_widget(template=tpl, data=dict(contents=content), scope=scope, position=position)


column = put_column
row = put_row
grid = put_grid


@safely_destruct_output_when_exp('contents')
def output(*contents):
    """返回一个handler，相当于 ``put_xxx()`` 的占位符，可以传入任何接收 ``put_xxx()`` 调用的地方，通过handler可对自身内容进行修改

    output用于对 :ref:`组合输出 <combine_output>` 中的 ``put_xxx()`` 子项进行动态修改（见下方代码示例）

    :param contents: 要输出的初始内容. 元素为 ``put_xxx()`` 形式的调用或字符串，字符串会被看成HTML.
    :return: OutputHandler 实例, 实例支持的方法如下:

    * ``reset(*contents)`` : 重置内容为 ``contents``
    * ``append(*contents)`` : 在末尾追加内容
    * ``insert(idx, *contents)`` : 插入内容. ``idx`` 表示内容插入位置:

       | idx>=0 时表示输出内容到原内容的idx索引的元素的前面；
       | idx<0 时表示输出内容到到原内容的idx索引元素之后.

    :Example:

    .. exportable-codeblock::
        :name: output
        :summary: 内容占位符——`output()`

        hobby = output(put_text('Coding'))
        put_table([
           ['Name', 'Hobbies'],
           ['Wang', hobby]      # hobby 初始为 Coding
        ])
        ## ----

        hobby.reset(put_text('Movie'))  # hobby 被重置为 Movie
        ## ----
        hobby.append(put_text('Music'), put_text('Drama'))   # 向 hobby 追加 Music, Drama
        ## ----
        hobby.insert(0, put_markdown('**Coding**'))  # 将 Coding 插入 hobby 顶端

    """

    class OutputHandler(Output):
        """与 Output 的不同在于， 不会在销毁时(__del__)自动输出"""

        def __del__(self):
            pass

        def __init__(self, spec, scope):
            super().__init__(spec)
            self.scope = scope

        @safely_destruct_output_when_exp('outputs')
        def reset(self, *outputs):
            clear_scope(scope=self.scope)
            self.append(*outputs)

        @safely_destruct_output_when_exp('outputs')
        def append(self, *outputs):
            for o in outputs:
                o.spec['scope'] = _parse_scope(self.scope)
                o.spec['position'] = OutputPosition.BOTTOM
                o.send()

        @safely_destruct_output_when_exp('outputs')
        def insert(self, idx, *outputs):
            """idx可为负，"""
            direction = 1 if idx >= 0 else -1
            for acc, o in enumerate(outputs):
                o.spec['scope'] = _parse_scope(self.scope)
                o.spec['position'] = idx + direction * acc
                o.send()

    dom_name = random_str(10)
    tpl = """<div class="{{dom_class_name}}">
            {{#contents}}
                {{#.}}
                    {{& pywebio_output_parse}}
                {{/.}}
            {{/contents}}
        </div>"""
    out_spec = put_widget(template=tpl,
                          data=dict(contents=contents, dom_class_name=_parse_scope(dom_name, no_css_selector=True)))
    return OutputHandler(Output.dump_dict(out_spec), ('.', dom_name))


@safely_destruct_output_when_exp('outputs')
def style(outputs, css_style) -> Union[Output, OutputList]:
    """自定义输出内容的css样式

    :param outputs: 输出内容，可以为 ``put_xxx()`` 调用或其列表。outputs为列表时将为每个列表项都添加自定义的css样式。
    :type outputs: list/put_xxx()
    :param css_style: css样式字符串
    :return: 添加了css样式的输出内容。

       | 若 ``outputs`` 为 ``put_xxx()`` 调用，返回值为添加了css样式的输出, 可用于任何接受 ``put_xxx()`` 类调用的地方。
       | 若 ``outputs`` 为list，返回值为 ``outputs`` 中每一项都添加了css样式的list, 可用于任何接受 ``put_xxx()`` 列表的地方。

    :Example:

    .. exportable-codeblock::
        :name: style
        :summary: 使用`style()`自定义内容样式

        style(put_text('Red'), 'color:red')

        ## ----
        style([
            put_text('Red'),
            put_markdown('~~del~~')
        ], 'color:red')

        ## ----
        put_table([
            ['A', 'B'],
            ['C', style(put_text('Red'), 'color:red')],
        ])

        ## ----
        put_collapse('title', style([
            put_text('text'),
            put_markdown('~~del~~'),
        ], 'margin-left:20px'))

    """
    if not isinstance(outputs, (list, tuple, OutputList)):
        ol = [outputs]
    else:
        ol = outputs
        outputs = OutputList(outputs)

    for o in ol:
        assert isinstance(o, Output), 'style() only accept put_xxx() input'
        o.spec.setdefault('style', '')
        o.spec['style'] += ';%s' % css_style

    return outputs


@safely_destruct_output_when_exp('content')
def popup(title, content=None, size=PopupSize.NORMAL, implicit_close=True, closable=True):
    """popup(title, content, size=PopupSize.NORMAL, implicit_close=True, closable=True)

    显示弹窗

    ⚠️: PyWebIO不允许同时显示多个弹窗，在显示新弹窗前，会自动关闭页面上存在的弹窗。可以使用 `close_popup()` 主动关闭弹窗

    :param str title: 弹窗标题
    :type content: list/str/put_xxx()
    :param content: 弹窗内容. 可以为字符串或 ``put_xxx`` 类输出函数的返回值，或者为它们组成的列表。
    :param str size: 弹窗窗口大小，可选值：

         * ``LARGE`` : 大尺寸
         * ``NORMAL`` : 普通尺寸
         * ``SMALL`` : 小尺寸

    :param bool implicit_close: 是否可以通过点击弹窗外的内容或按下 ``Esc`` 键来关闭弹窗
    :param bool closable: 是否可由用户关闭弹窗. 默认情况下，用户可以通过点击弹窗右上角的关闭按钮来关闭弹窗，
       设置为 ``False`` 时弹窗仅能通过 :func:`popup_close()` 关闭， ``implicit_close`` 参数被忽略.

    支持直接传入内容、上下文管理器、装饰器三种形式的调用

    * 直接传入内容:

    .. exportable-codeblock::
        :name: popup
        :summary: 直接调用`popup()`来显示弹窗

        popup('popup title', 'popup text content', size=PopupSize.SMALL)
        ## ----

        popup('Popup title', [
            put_html('<h3>Popup Content</h3>'),
            'html: <br/>',
            put_table([['A', 'B'], ['C', 'D']]),
            put_buttons(['close_popup()'], onclick=lambda _: close_popup())
        ])

    * 作为上下文管理器使用:

    .. exportable-codeblock::
        :name: popup-context
        :summary: 将`popup()`作为下文管理器来创建弹窗

        with popup('Popup title') as s:
            put_html('<h3>Popup Content</h3>')
            put_text('html: <br/>')
            put_buttons(['clear()'], onclick=lambda _: clear(scope=s))

        put_text('Also work!', scope=s)


    上下文管理器会开启一个新的输出域并返回Scope名，上下文管理器中的输出调用会显示到弹窗上。
    上下文管理器退出后，弹窗并不会关闭，依然可以使用 ``scope`` 参数输出内容到弹窗。

    * 作为装饰器使用:

    .. exportable-codeblock::
        :name: popup-context
        :summary: 将`popup()`作为装饰器使用

        @popup('Popup title')
        def show_popup():
            put_html('<h3>Popup Content</h3>')
            put_text("I'm in a popup!")
            ...

        show_popup()

    """
    if content is None:
        content = []

    if not isinstance(content, (list, tuple, OutputList)):
        content = [content]

    for item in content:
        assert isinstance(item, (str, Output)), "popup() content must be list of str/put_xxx()"

    dom_id = random_str(10)

    send_msg(cmd='popup', spec=dict(content=Output.dump_dict(content), title=title, size=size,
                                    implicit_close=implicit_close, closable=closable,
                                    dom_id=_parse_scope(dom_id, no_css_selector=True)))

    return use_scope_(dom_id)


def close_popup():
    """关闭当前页面上正在显示的弹窗"""
    send_msg(cmd='close_popup')


def toast(content, duration=2, position='center', color='info', onclick=None):
    """显示一条通知消息

    :param str content: 通知内容
    :param float duration: 通知显示持续的时间，单位为秒。 `0` 表示不自动关闭(此时消息旁会显示一个关闭图标，用户可以手动关闭消息)
    :param str position: 通知消息显示的位置，可以为 `'left'` / `'center'` / `'right'`
    :param str color: 通知消息的背景颜色，可以为 `'info'` / `'error'` / `'warn'` / `'success'` 或以 `'#'` 开始的十六进制颜色值
    :param callable onclick: 点击通知消息时的回调函数，回调函数不接受任何参数。

        Note: 当使用 :ref:`基于协程的会话实现 <coroutine_based_session>` 时，回调函数可以为协程函数.

    Example:

    .. exportable-codeblock::
        :name: toast
        :summary: 使用`toast()`显示通知

        def show_msg():
            put_text("Some messages...")

        toast('New messages', position='right', color='#2188ff', duration=0, onclick=show_msg)

    """

    colors = {
        'info': '#1565c0',
        'error': '#e53935',
        'warn': '#ef6c00',
        'success': '#2e7d32'
    }
    color = colors.get(color, color)
    callback_id = output_register_callback(lambda _: onclick()) if onclick is not None else None

    send_msg(cmd='toast', spec=dict(content=content, duration=int(duration * 1000), position=position,
                                    color=color, callback_id=callback_id))


clear_scope = clear


def use_scope(name=None, clear=False, create_scope=True, **scope_params):
    """scope的上下文管理器和装饰器。用于创建一个新的输出域并进入，或进入一个已经存在的输出域。

    参见 :ref:`用户手册-use_scope() <use_scope>`

    :param name: scope名. 若为None则生成一个全局唯一的scope名.（以上下文管理器形式的调用时，上下文管理器会返回scope名）
    :param bool clear: 在进入scope前是否要清除scope里的内容
    :param bool create_scope: scope不存在时是否创建scope
    :param scope_params: 创建scope时传入set_scope()的参数. 仅在 `create_scope=True` 时有效.

    :Usage:

    ::

        with use_scope(...) as scope_name:
            put_xxx()

        @use_scope(...)
        def app():
            put_xxx()

    """
    if name is None:
        name = random_str(10)
    else:
        assert is_html_safe_value(name), "Scope name only allow letter/digit/'_'/'-' char."

    def before_enter():
        if create_scope:
            set_scope(name, **scope_params)

        if clear:
            clear_scope(name)

    return use_scope_(name=name, before_enter=before_enter)


class use_scope_:
    def __init__(self, name, before_enter=None):
        self.before_enter = before_enter
        self.name = name

    def __enter__(self):
        if self.before_enter:
            self.before_enter()
        get_current_session().push_scope(self.name)
        return self.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        """该方法如果返回True ，说明上下文管理器可以处理异常，使得 with 语句终止异常传播"""
        get_current_session().pop_scope()
        return False  # Propagate Exception

    def __call__(self, func):
        """装饰器"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            self.__enter__()
            try:
                return func(*args, **kwargs)
            finally:
                self.__exit__(None, None, None)

        @wraps(func)
        async def coro_wrapper(*args, **kwargs):
            self.__enter__()
            try:
                return await func(*args, **kwargs)
            finally:
                self.__exit__(None, None, None)

        if iscoroutinefunction(func):
            return coro_wrapper
        else:
            return wrapper
