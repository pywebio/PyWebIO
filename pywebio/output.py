r"""输出内容到用户浏览器

本模块提供了一系列函数来输出不同形式的内容到用户浏览器，并支持灵活的输出控制。

输出控制
--------------

锚点
^^^^^^^^^^^^^^^^^

.. autofunction:: set_anchor
.. autofunction:: clear_before
.. autofunction:: clear_after
.. autofunction:: clear_range
.. autofunction:: remove
.. autofunction:: scroll_to

环境设置
^^^^^^^^^^^^^^^^^

.. autofunction:: set_title
.. autofunction:: set_output_fixed_height
.. autofunction:: set_auto_scroll_bottom

内容输出
--------------
.. autofunction:: put_text
.. autofunction:: put_markdown
.. autofunction:: put_html
.. autofunction:: put_code
.. autofunction:: put_table
.. autofunction:: table_cell_buttons
.. autofunction:: put_buttons
.. autofunction:: put_image
.. autofunction:: put_file
"""
import io
import json
import logging
from base64 import b64encode
from collections.abc import Mapping

from .io_ctrl import output_register_callback, send_msg, OutputReturn, safely_destruct_output_when_exp

try:
    from PIL.Image import Image as PILImage
except ImportError:
    PILImage = type('MockPILImage', (), dict(__init__=None))

logger = logging.getLogger(__name__)

__all__ = ['TOP', 'MIDDLE', 'BOTTOM', 'set_title', 'set_output_fixed_height', 'set_auto_scroll_bottom', 'set_anchor',
           'clear_before', 'clear_after', 'clear_range', 'remove', 'scroll_to', 'put_text', 'put_html',
           'put_code', 'put_markdown', 'put_table', 'table_cell_buttons', 'put_buttons', 'put_image', 'put_file', ]

TOP = 'top'
MIDDLE = 'middle'
BOTTOM = 'bottom'


def set_title(title):
    r"""设置页面标题"""
    send_msg('output_ctl', dict(title=title))


def set_output_fixed_height(enabled=True):
    r"""开启/关闭页面固高度模式"""
    send_msg('output_ctl', dict(output_fixed_height=enabled))


def set_auto_scroll_bottom(enabled=True):
    r"""开启/关闭页面自动滚动到底部"""
    send_msg('output_ctl', dict(auto_scroll_bottom=enabled))


def _get_anchor_id(name):
    """获取实际用于前端html页面中的id属性"""
    name = name.replace(' ', '-')
    return 'pywebio-anchor-%s' % name


def set_anchor(name):
    """
    在当前输出处标记锚点。 若已经存在 ``name`` 锚点，则先将旧锚点删除
    """
    inner_ancher_name = _get_anchor_id(name)
    send_msg('output_ctl', dict(set_anchor=inner_ancher_name))


def clear_before(anchor):
    """清除 ``anchor`` 锚点之前输出的内容。
    ⚠️注意: 位于 ``anchor`` 锚点之前设置的锚点也会被清除
    """
    inner_ancher_name = _get_anchor_id(anchor)
    send_msg('output_ctl', dict(clear_before=inner_ancher_name))


def clear_after(anchor):
    """清除 ``anchor`` 锚点之后输出的内容。
    ⚠️注意: 位于 ``anchor`` 锚点之后设置的锚点也会被清除
    """
    inner_ancher_name = _get_anchor_id(anchor)
    send_msg('output_ctl', dict(clear_after=inner_ancher_name))


def clear_range(start_anchor, end_anchor):
    """
    清除 ``start_anchor`` - ``end_ancher`` 锚点之间输出的内容.
    若 ``start_anchor`` 或 ``end_ancher`` 不存在，则不进行任何操作。

    ⚠️注意: 在 ``start_anchor`` - ``end_ancher`` 之间设置的锚点也会被清除
    """
    inner_start_anchor_name = 'pywebio-anchor-%s' % start_anchor
    inner_end_ancher_name = 'pywebio-anchor-%s' % end_anchor
    send_msg('output_ctl', dict(clear_range=[inner_start_anchor_name, inner_end_ancher_name]))


def remove(anchor):
    """将 ``anchor`` 锚点连同锚点处的内容移除"""
    inner_ancher_name = _get_anchor_id(anchor)
    send_msg('output_ctl', dict(remove=inner_ancher_name))


def scroll_to(anchor, position=TOP):
    """将页面滚动到 ``anchor`` 锚点处

    :param str anchor: 锚点名
    :param str position: 将锚点置于屏幕可视区域的位置。可用值：

       * ``TOP`` : 滚动页面，让锚点位于屏幕可视区域顶部
       * ``MIDDLE`` : 滚动页面，让锚点位于屏幕可视区域中间
       * ``BOTTOM`` : 滚动页面，让锚点位于屏幕可视区域底部
    """
    inner_ancher_name = 'pywebio-anchor-%s' % anchor
    send_msg('output_ctl', dict(scroll_to=inner_ancher_name, position=position))


def _get_output_spec(type, anchor=None, before=None, after=None, **other_spec):
    """
    获取 ``output`` 指令的spec字段

    :param str type: 输出类型
    :param content: 输出内容
    :param str anchor: 为当前的输出内容标记锚点，若锚点已经存在，则将锚点处的内容替换为当前内容。
    :param str before: 在给定的锚点之前输出内容。若给定的锚点不存在，则不输出任何内容
    :param str after: 在给定的锚点之后输出内容。若给定的锚点不存在，则不输出任何内容。
        注意： ``before`` 和 ``after`` 参数不可以同时使用
    :param other_spec: 额外的输出参数，值为None的参数不会包含到返回值中

    :return dict:  ``output`` 指令的spec字段
    """
    assert not (before and after), "Parameter 'before' and 'after' cannot be specified at the same time"

    spec = dict(type=type)
    spec.update({k: v for k, v in other_spec.items() if v is not None})
    if anchor:
        spec['anchor'] = _get_anchor_id(anchor)
    if before:
        spec['before'] = _get_anchor_id(before)
    elif after:
        spec['after'] = _get_anchor_id(after)

    return spec


def put_text(text, inline=False, anchor=None, before=None, after=None) -> OutputReturn:
    """
    输出文本内容

    :param str text: 文本内容
    :param bool inline: 文本行末不换行。默认换行
    :param str anchor: 为当前的输出内容标记锚点，若锚点已经存在，则将锚点处的内容替换为当前内容。
    :param str before: 在给定的锚点之前输出内容。若给定的锚点不存在，则不输出任何内容
    :param str after: 在给定的锚点之后输出内容。若给定的锚点不存在，则不输出任何内容。

    注意： ``before`` 和 ``after`` 参数不可以同时使用。
    当 ``anchor`` 指定的锚点已经在页面上存在时，``before`` 和 ``after`` 参数将被忽略。
    """
    spec = _get_output_spec('text', content=str(text), inline=inline, anchor=anchor, before=before, after=after)
    return OutputReturn(spec)


def put_html(html, anchor=None, before=None, after=None) -> OutputReturn:
    """
    输出Html内容。

    与支持通过Html输出内容到 `Jupyter Notebook <https://nbviewer.jupyter.org/github/ipython/ipython/blob/master/examples/IPython%20Kernel/Rich%20Output.ipynb#HTML>`_ 的库兼容。

    :param html: html字符串或 实现了 `IPython.display.HTML` 接口的类的实例
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    if hasattr(html, '__html__'):
        html = html.__html__()

    spec = _get_output_spec('html', content=html, anchor=anchor, before=before, after=after)
    return OutputReturn(spec)


def put_code(content, langage='', anchor=None, before=None, after=None) -> OutputReturn:
    """
    输出代码块

    :param str content: 代码内容
    :param str langage: 代码语言
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    code = "```%s\n%s\n```" % (langage, content)
    return put_markdown(code, anchor=anchor, before=before, after=after)


def put_markdown(mdcontent, strip_indent=0, lstrip=False, anchor=None, before=None, after=None) -> OutputReturn:
    """
    输出Markdown内容。

    :param str mdcontent: Markdown文本
    :param int strip_indent: 对于每一行，若前 ``strip_indent`` 个字符都为空格，则将其去除
    :param bool lstrip: 是否去除每一行开始的空白符
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致

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

    spec = _get_output_spec('markdown', content=mdcontent, anchor=anchor, before=before, after=after)
    return OutputReturn(spec)


@safely_destruct_output_when_exp('tdata')
def put_table(tdata, header=None, span=None, anchor=None, before=None, after=None) -> OutputReturn:
    """
    输出表格

    :param list tdata: 表格数据。列表项可以为 ``list`` 或者 ``dict`` , 单元格的内容可以为字符串或 ``put_xxx`` 类型的输出函数，字符串内容的单元格显示时会被当作html。
    :param list header: 设定表头。
       当 ``tdata`` 的列表项为 ``list`` 类型时，若省略 ``header`` 参数，则使用 ``tdata`` 的第一项作为表头。

       当 ``tdata`` 为字典列表时，使用 ``header`` 指定表头顺序，不可省略。
       此时， ``header`` 格式可以为 <字典键>列表 或者 ``(<显示文本>, <字典键>)`` 列表。

    :param dict span: 表格的跨行/跨列信息，格式为 ``{ (行id,列id):{"col": 跨列数, "row": 跨行数} }``
       其中 ``行id`` 和 ``列id`` 为将表格转为二维数组后的需要跨行/列的单元格，二维数据包含表头，``id`` 从 0 开始记数。
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致

    使用示例::

        # 'Name'单元格跨2行、'Address'单元格跨2列
        put_table([
            ['Name', 'Address'],
            ['City', 'Country'],
            ['Wang', 'Beijing', 'China'],
            ['Liu', 'New York', 'America'],
        ], span={(0,0):{"row":2}, (0,1):{"col":2}})

        # 单元格为 ``put_xxx`` 类型的输出函数
        put_table([
            ['Type', 'Content'],
            ['html', 'X<sup>2</sup>'],
            ['text', put_text('<hr/>')],
            ['buttons', put_buttons(['A', 'B'], onclick=...)],
            ['markdown', put_markdown('`Awesome PyWebIO!`')],
            ['file', put_file('hello.text', b'')],
            ['table', put_table([['A', 'B'], ['C', 'D']])]
        ])

        # 设置表头
        put_table([
            ['Wang', 'M', 'China'],
            ['Liu', 'W', 'America'],
        ], header=['Name', 'Gender', 'Address'])

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

    if header:
        tdata = [header, *tdata]

    span = span or {}
    span = {('%s,%s' % row_col): val for row_col, val in span.items()}

    spec = _get_output_spec('table', data=tdata, span=span, anchor=anchor, before=before, after=after)
    return OutputReturn(spec)


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


def table_cell_buttons(buttons, onclick, **callback_options) -> str:
    """
    在表格中显示一组按钮

    :param str buttons, onclick, save: 与 `put_buttons` 函数的同名参数含义一致

    .. _table_cell_buttons-code-sample:

    使用示例::

        from functools import partial

        def edit_row(choice, row):
            put_text("You click %s button at row %s" % (choice, row))

        put_table([
            ['Idx', 'Actions'],
            ['1', table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
            ['2', table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
            ['3', table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
        ])

    .. deprecated:: 0.3
       Use :func:`put_buttons()` instead
    """
    logger.warning("pywebio.output.table_cell_buttons() is deprecated in version 0.3 and will be removed in 1.0, "
                   "use pywebio.output.put_buttons() instead.")
    btns = _format_button(buttons)
    callback_id = output_register_callback(onclick, **callback_options)
    tpl = '<button type="button" value="{value}" class="btn btn-primary btn-sm" ' \
          'onclick="WebIO.DisplayAreaButtonOnClick(this, \'%s\')">{label}</button>' % callback_id
    btns_html = [tpl.format(**b) for b in btns]
    return ' '.join(btns_html)


def put_buttons(buttons, onclick, small=None, anchor=None, before=None, after=None,
                **callback_options) -> OutputReturn:
    """
    输出一组按钮

    :param list buttons: 按钮列表。列表项的可用形式有：

        * dict: ``{label:选项标签, value:选项值}``
        * tuple or list: ``(label, value)``
        * 单值: 此时label和value使用相同的值

    :type onclick: Callable or Coroutine
    :param onclick: 按钮点击回调函数. ``onclick`` 可以是普通函数或者协程函数.
       函数签名为 ``onclick(btn_value)``.
       当按钮组中的按钮被点击时，``onclick`` 被调用，并传入被点击的按钮的 ``value`` 值。
       可以使用 ``functools.partial`` 来在 ``onclick`` 中保存更多上下文信息 。
    :param bool small: 是否显示小号按钮，默认为False
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    :param callback_options: 回调函数的其他参数。根据选用的 session 实现有不同参数

       CoroutineBasedSession 实现
           * mutex_mode: 互斥模式。默认为 ``False`` 。若为 ``True`` ，则在运行回调函数过程中，无法响应当前按钮组的新点击事件，仅当 ``onclick`` 为协程函数时有效

       ThreadBasedSession 实现
           * serial_mode: 串行模式模式。默认为 ``False`` 。若为 ``True`` ，则运行当前点击事件时，其他所有新的点击事件都将被排队等待当前点击事件时运行完成。
             不开启 ``serial_mode`` 时，ThreadBasedSession 在新线程中执行回调函数。所以如果回调函数运行时间很短，
             可以关闭 ``serial_mode`` 来提高性能。

    使用示例::

        from functools import partial

        def edit_row(choice, id):
            put_text("You click %s button with id: %s" % (choice, id))

        put_buttons(['edit', 'delete'], onclick=partial(edit_row, id=1))

    """
    btns = _format_button(buttons)
    callback_id = output_register_callback(onclick, **callback_options)
    spec = _get_output_spec('buttons', callback_id=callback_id, buttons=btns, small=small, anchor=anchor, before=before,
                            after=after)

    def on_embed(spec):
        spec.setdefault('small', True)
        return spec

    return OutputReturn(spec, on_embed=on_embed)


def put_image(content, format=None, title='', width=None, height=None, anchor=None, before=None,
              after=None) -> OutputReturn:
    """输出图片。

    :param content: 文件内容. 类型为 bytes-like object 或者为 ``PIL.Image.Image`` 实例
    :param str title: 图片描述
    :param str width: 图像的宽度，单位是CSS像素(数字px)或者百分比(数字%)。
    :param str height: 图像的高度，单位是CSS像素(数字px)或者百分比(数字%)。可以只指定 width 和 height 中的一个值，浏览器会根据原始图像进行缩放。
    :param str format: 图片格式。如 ``png`` , ``jpeg`` , ``gif`` 等
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    if isinstance(content, PILImage):
        format = content.format
        imgByteArr = io.BytesIO()
        content.save(imgByteArr, format=format)
        content = imgByteArr.getvalue()

    format = '' if format is None else ('image/%s' % format)

    width = 'width="%s"' % width if width is not None else ''
    height = 'height="%s"' % height if height is not None else ''

    b64content = b64encode(content).decode('ascii')
    html = r'<img src="data:{format};base64, {b64content}" ' \
           r'alt="{title}" {width} {height}/>'.format(format=format, b64content=b64content,
                                                      title=title, height=height, width=width)
    return put_html(html, anchor=anchor, before=before, after=after)


def put_file(name, content, anchor=None, before=None, after=None) -> OutputReturn:
    """输出文件。
    在浏览器上的显示为一个以文件名为名的链接，点击链接后浏览器自动下载文件。

    :param str name: 文件名
    :param content: 文件内容. 类型为 bytes-like object
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    content = b64encode(content).decode('ascii')
    spec = _get_output_spec('file', name=name, content=content, anchor=anchor, before=before, after=after)
    return OutputReturn(spec)

