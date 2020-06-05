r"""输出内容到用户浏览器

本模块提供了一系列函数来输出不同形式的内容到用户浏览器，并支持灵活的输出控制。

输出控制
--------------

输出域Scope
^^^^^^^^^^^^^^^^^

.. autofunction:: set_scope
.. autofunction:: clear
.. autofunction:: remove
.. autofunction:: scroll_to
.. autofunction:: use_scope


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
.. autofunction:: put_collapse

.. autofunction:: put_widget
"""
import io
import logging
from base64 import b64encode
from collections.abc import Mapping
from functools import wraps

from .io_ctrl import output_register_callback, send_msg, OutputReturn, safely_destruct_output_when_exp
from .session import get_current_session
from .utils import random_str, iscoroutinefunction

try:
    from PIL.Image import Image as PILImage
except ImportError:
    PILImage = type('MockPILImage', (), dict(__init__=None))

logger = logging.getLogger(__name__)

__all__ = ['Position', 'set_title', 'set_output_fixed_height', 'set_auto_scroll_bottom', 'remove', 'scroll_to',
           'put_text', 'put_html', 'put_code', 'put_markdown', 'use_scope', 'set_scope', 'clear', 'remove',
           'put_table', 'table_cell_buttons', 'put_buttons', 'put_image', 'put_file', 'PopupSize', 'popup',
           'close_popup', 'put_widget', 'put_collapse']


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


def set_title(title):
    r"""设置页面标题"""
    send_msg('output_ctl', dict(title=title))


def set_output_fixed_height(enabled=True):
    r"""开启/关闭页面固高度模式"""
    send_msg('output_ctl', dict(output_fixed_height=enabled))


def set_auto_scroll_bottom(enabled=True):
    r"""开启/关闭页面自动滚动到底部"""
    send_msg('output_ctl', dict(auto_scroll_bottom=enabled))


def _parse_scope(name):
    """获取实际用于前端html页面中的id属性

    :param str name:
    """
    name = name.replace(' ', '-')
    return 'pywebio-scope-%s' % name


def set_scope(name, container_scope=Scope.Current, position=OutputPosition.BOTTOM, if_exist='none'):
    """创建一个新的scope.

    :param str name: scope名
    :param int/str container_scope: 此scope的父scope. 可以直接指定父scope名或使用 `Scope` 常量. scope不存在时，不进行任何操作.
    :param int position: 在父scope中创建此scope的位置.
       `OutputPosition.TOP` : 在父scope的顶部创建, `OutputPosition.BOTTOM` : 在父scope的尾部创建
    :param str if_exist: 已经存在 ``name`` scope 时如何操作:

        - `'none'` 表示不进行任何操作
        - `'remove'` 表示先移除旧scope再创建新scope
        - `'clear'` 表示将旧scope的内容清除，不创建新scope

       默认为 `'none'`
    """
    if isinstance(container_scope, int):
        container_scope = get_current_session().get_scope_name(container_scope)

    send_msg('output_ctl', dict(set_scope=_parse_scope(name),
                                container=_parse_scope(container_scope),
                                position=position, if_exist=if_exist))


def clear(scope=Scope.Current):
    """清空scope内容

    :param int/str scope: 可以直接指定scope名或使用 `Scope` 常量
    """
    scope_name = _parse_scope(scope)
    send_msg('output_ctl', dict(clear=scope_name))


def remove(scope):
    """移除Scope"""
    send_msg('output_ctl', dict(remove=_parse_scope(scope)))


def scroll_to(scope, position=Position.TOP):
    """scroll_to(scope, position=Position.TOP)

    将页面滚动到 ``scope`` Scope处

    :param str scope: Scope名
    :param str position: 将Scope置于屏幕可视区域的位置。可用值：

       * ``Position.TOP`` : 滚动页面，让Scope位于屏幕可视区域顶部
       * ``Position.MIDDLE`` : 滚动页面，让Scope位于屏幕可视区域中间
       * ``Position.BOTTOM`` : 滚动页面，让Scope位于屏幕可视区域底部
    """
    send_msg('output_ctl', dict(scroll_to=_parse_scope(scope), position=position))


def _get_output_spec(type, scope, position, **other_spec):
    """
    获取 ``output`` 指令的spec字段

    :param str type: 输出类型
    :param int/str scope: 输出到的scope
    :param int position: 在scope输出的位置， `OutputPosition.TOP` : 输出到scope的顶部， `OutputPosition.BOTTOM` : 输出到scope的尾部
    :param other_spec: 额外的输出参数，值为None的参数不会包含到返回值中

    :return dict:  ``output`` 指令的spec字段
    """
    spec = dict(type=type)
    spec.update({k: v for k, v in other_spec.items() if v is not None})

    if isinstance(scope, int):
        scope_name = get_current_session().get_scope_name(scope)
    else:
        scope_name = scope

    spec['scope'] = _parse_scope(scope_name)
    spec['position'] = position

    return spec


def put_text(text, inline=False, scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """
    输出文本内容

    :param any text: 文本内容
    :param bool inline: 文本行末不换行。默认换行
    :param int/str scope: 内容输出的目标scope, 若scope不存在，则不进行任何输出操作。
       `scope` 可以直接指定目标Scope名，或者使用int通过索引Scope栈来确定Scope：0表示最顶层也就是ROOT Scope，-1表示当前Scope，-2表示当前Scope的父Scope，...
    :param int position: 在scope中输出的位置。
       position为非负数时表示输出到scope的第position个(从0计数)子元素的前面；position为负数时表示输出到scope的倒数第position个(从-1计数)元素之后。

    参数 `scope` 和 `position` 的更多使用说明参见 :ref:`用户手册 <scope_param>`
    """
    spec = _get_output_spec('text', content=str(text), inline=inline, scope=scope, position=position)
    return OutputReturn(spec)


def put_html(html, scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """
    输出Html内容。

    与支持通过Html输出内容到 `Jupyter Notebook <https://nbviewer.jupyter.org/github/ipython/ipython/blob/master/examples/IPython%20Kernel/Rich%20Output.ipynb#HTML>`_ 的库兼容。

    :param html: html字符串或 实现了 `IPython.display.HTML` 接口的类的实例
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    if hasattr(html, '__html__'):
        html = html.__html__()

    spec = _get_output_spec('html', content=html, scope=scope, position=position)
    return OutputReturn(spec)


def put_code(content, langage='', scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """
    输出代码块

    :param str content: 代码内容
    :param str langage: 代码语言
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    code = "```%s\n%s\n```" % (langage, content)
    return put_markdown(code, scope=scope, position=position)


def put_markdown(mdcontent, strip_indent=0, lstrip=False, scope=Scope.Current,
                 position=OutputPosition.BOTTOM) -> OutputReturn:
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
    return OutputReturn(spec)


@safely_destruct_output_when_exp('tdata')
def put_table(tdata, header=None, span=None, scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """
    输出表格

    :param list tdata: 表格数据。列表项可以为 ``list`` 或者 ``dict`` , 单元格的内容可以为字符串或 ``put_xxx`` 类型的输出函数，字符串内容的单元格显示时会被当作html。
    :param list header: 设定表头。
       当 ``tdata`` 的列表项为 ``list`` 类型时，若省略 ``header`` 参数，则使用 ``tdata`` 的第一项作为表头。

       当 ``tdata`` 为字典列表时，使用 ``header`` 指定表头顺序，不可省略。
       此时， ``header`` 格式可以为 <字典键>列表 或者 ``(<显示文本>, <字典键>)`` 列表。

    :param dict span: 表格的跨行/跨列信息，格式为 ``{ (行id,列id):{"col": 跨列数, "row": 跨行数} }``
       其中 ``行id`` 和 ``列id`` 为将表格转为二维数组后的需要跨行/列的单元格，二维数据包含表头，``id`` 从 0 开始记数。
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

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

    spec = _get_output_spec('table', data=tdata, span=span, scope=scope, position=position)
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


def put_buttons(buttons, onclick, small=None, scope=Scope.Current, position=OutputPosition.BOTTOM,
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
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
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
    spec = _get_output_spec('buttons', callback_id=callback_id, buttons=btns, small=small,
                            scope=scope, position=position)

    return OutputReturn(spec)


def put_image(content, format=None, title='', width=None, height=None,
              scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """输出图片。

    :param content: 文件内容. 类型为 bytes-like object 或者为 ``PIL.Image.Image`` 实例
    :param str title: 图片描述
    :param str width: 图像的宽度，单位是CSS像素(数字px)或者百分比(数字%)。
    :param str height: 图像的高度，单位是CSS像素(数字px)或者百分比(数字%)。可以只指定 width 和 height 中的一个值，浏览器会根据原始图像进行缩放。
    :param str format: 图片格式。如 ``png`` , ``jpeg`` , ``gif`` 等
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
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
    return put_html(html, scope=scope, position=position)


def put_file(name, content, scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """输出文件。
    在浏览器上的显示为一个以文件名为名的链接，点击链接后浏览器自动下载文件。

    :param str name: 文件名
    :param content: 文件内容. 类型为 bytes-like object
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    content = b64encode(content).decode('ascii')
    spec = _get_output_spec('file', name=name, content=content, scope=scope, position=position)
    return OutputReturn(spec)


@safely_destruct_output_when_exp('content')
def put_collapse(title, content, open=False, scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """输出可折叠的内容

    :param str title: 内容标题
    :type content: list/str/put_xxx()
    :param content: 内容可以为字符串或 ``put_xxx`` 类输出函数的返回值，或者为它们组成的列表。字符串内容会被看作html
    :param bool open: 是否默认展开折叠内容。默认不展开内容
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致
    """
    if not isinstance(content, (list, tuple)):
        content = [content]

    for item in content:
        assert isinstance(item, (str, OutputReturn)), "put_collapse() content must be list of str/put_xxx()"

    tpl = """
    <details {{#open}}open{{/open}}>
        <summary>{{title}}</summary>
        {{#contents}}
            {{& pywebio_output_parse}}
        {{/contents}}
    </details>
    """
    return put_widget(tpl, dict(title=title, contents=content, open=open), scope=scope, position=position)


@safely_destruct_output_when_exp('data')
def put_widget(template, data, scope=Scope.Current, position=OutputPosition.BOTTOM) -> OutputReturn:
    """输出自定义的控件

    :param template: html模版，使用 `mustache.js <https://github.com/janl/mustache.js>`_ 语法
    :param dict data:  渲染模版使用的数据.

       数据可以包含输出函数( ``put_xxx()`` )的返回值, 可以使用 ``pywebio_output_parse`` 函数来解析 ``put_xxx()`` 内容.

       ⚠️：使用 ``pywebio_output_parse`` 函数时，需要关闭mustache的html转义: ``{{& pywebio_output_parse}}`` , 参见下文示例.
    :param int scope, position: 与 `put_text` 函数的同名参数含义一致

    :Example:
    ::

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
                put_text('text'),
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
    return OutputReturn(spec)


@safely_destruct_output_when_exp('content')
def popup(title, content, size=PopupSize.NORMAL, implicit_close=True, closable=True):
    """popup(title, content, size=PopupSize.NORMAL, implicit_close=True, closable=True)

    显示弹窗

    :param str title: 弹窗标题
    :type content: list/str/put_xxx()
    :param content: 弹窗内容. 可以为字符串或 ``put_xxx`` 类输出函数的返回值，或者为它们组成的列表。字符串内容会被看作html
    :param str size: 弹窗窗口大小，可选值：

         * ``LARGE`` : 大尺寸
         * ``NORMAL`` : 普通尺寸
         * ``SMALL`` : 小尺寸

    :param bool implicit_close: 是否可以通过点击弹窗外的内容或按下 ``Esc`` 键来关闭弹窗
    :param bool closable: 是否可由用户关闭弹窗. 默认情况下，用户可以通过点击弹窗右上角的关闭按钮来关闭弹窗，
       设置为 ``False`` 时弹窗仅能通过 :func:`popup_close()` 关闭， ``implicit_close`` 参数被忽略.

    Example::

        popup('popup title', 'popup html content', size=PopupSize.SMALL)

        popup('Popup title', [
            '<h3>Popup Content</h3>',
            put_text('html: <br/>'),
            put_table([['A', 'B'], ['C', 'D']]),
            put_buttons(['close_popup()'], onclick=lambda _: close_popup())
        ])

    """
    if not isinstance(content, (list, tuple)):
        content = [content]

    for item in content:
        assert isinstance(item, (str, OutputReturn)), "popup() content must be list of str/put_xxx()"

    send_msg(cmd='popup', spec=dict(content=OutputReturn.jsonify(content), title=title, size=size,
                                    implicit_close=implicit_close, closable=closable))


def close_popup():
    """关闭弹窗"""
    send_msg(cmd='close_popup')


clear_scope = clear


def use_scope(name=None, clear=False, create_scope=True, **scope_params):
    """scope的上下文管理器和装饰器

    :param name: scope名. 若为None则生成一个全局唯一的scope名
    :param bool clear: 是否要清除scope内容
    :param bool create_scope: scope不存在时是否创建scope
    :param scope_params: 创建scope时传入set_scope()的参数. 仅在 `create_scope=True` 时有效.

    :Usage:
    ::

        with use_scope(...):
            put_xxx()

        @use_scope(...)
        def app():
            put_xxx()
    """
    if name is None:
        name = random_str(10)

    class use_scope_:
        def __enter__(self):
            if create_scope:
                set_scope(name, **scope_params)

            if clear:
                clear_scope(name)

            get_current_session().push_scope(name)
            return name

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

    return use_scope_()
