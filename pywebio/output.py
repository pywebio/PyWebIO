r"""
This module provides functions to output all kinds of content to the user's browser, and supply flexible output control.


.. _output_func_list:


Functions list
---------------
..
  Use https://www.tablesgenerator.com/text_tables to generate/update below table

| The following table shows the output-related functions provided by PyWebIO.
| The functions marked with ``*`` indicate that they accept ``put_xxx`` calls as arguments.
| The functions marked with ``†`` indicate that they can use as context manager.

+--------------------+---------------------------+------------------------------------------------------------+
|                    | **Name**                  | **Description**                                            |
+--------------------+---------------------------+------------------------------------------------------------+
| Output Scope       | `put_scope`               | Create a new scope                                         |
|                    +---------------------------+------------------------------------------------------------+
|                    | `use_scope`:sup:`†`       | Enter a scope                                              |
|                    +---------------------------+------------------------------------------------------------+
|                    | `get_scope`               | Get the current scope name in the runtime scope stack      |
|                    +---------------------------+------------------------------------------------------------+
|                    | `clear`                   | Clear the content of scope                                 |
|                    +---------------------------+------------------------------------------------------------+
|                    | `remove`                  | Remove the scope                                           |
|                    +---------------------------+------------------------------------------------------------+
|                    | `scroll_to`               | Scroll the page to the scope                               |
+--------------------+---------------------------+------------------------------------------------------------+
| Content Outputting | `put_text`                | Output plain text                                          |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_markdown`            | Output Markdown                                            |
|                    +---------------------------+------------------------------------------------------------+
|                    | | `put_info`:sup:`*†`     | Output Messages.                                           |
|                    | | `put_success`:sup:`*†`  |                                                            |
|                    | | `put_warning`:sup:`*†`  |                                                            |
|                    | | `put_error`:sup:`*†`    |                                                            |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_html`                | Output html                                                |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_link`                | Output link                                                |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_processbar`          | Output a process bar                                       |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_loading`:sup:`†`     | Output loading prompt                                      |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_code`                | Output code block                                          |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_table`:sup:`*`       | Output table                                               |
|                    +---------------------------+------------------------------------------------------------+
|                    | | `put_button`            | Output button and bind click event                         |
|                    | | `put_buttons`           |                                                            |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_image`               | Output image                                               |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_file`                | Output a link to download a file                           |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_tabs`:sup:`*`        | Output tabs                                                |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_collapse`:sup:`*†`   | Output collapsible content                                 |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_scrollable`:sup:`*†` | | Output a fixed height content area,                      |
|                    |                           | | scroll bar is displayed when the content                 |
|                    |                           | | exceeds the limit                                        |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_widget`:sup:`*`      | Output your own widget                                     |
+--------------------+---------------------------+------------------------------------------------------------+
| Other Interactions | `toast`                   | Show a notification message                                |
|                    +---------------------------+------------------------------------------------------------+
|                    | `popup`:sup:`*†`          | Show popup                                                 |
|                    +---------------------------+------------------------------------------------------------+
|                    | `close_popup`             | Close the current popup window.                            |
+--------------------+---------------------------+------------------------------------------------------------+
| Layout and Style   | `put_row`:sup:`*†`        | Use row layout to output content                           |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_column`:sup:`*†`     | Use column layout to output content                        |
|                    +---------------------------+------------------------------------------------------------+
|                    | `put_grid`:sup:`*`        | Output content using grid layout                           |
|                    +---------------------------+------------------------------------------------------------+
|                    | `span`                    | Cross-cell content                                         |
|                    +---------------------------+------------------------------------------------------------+
|                    | `style`:sup:`*`           | Customize the css style of output content                  |
+--------------------+---------------------------+------------------------------------------------------------+

Output Scope
--------------

.. seealso::

   * :ref:`Use Guide: Output Scope <output_scope>`

.. autofunction:: put_scope
.. autofunction:: use_scope
.. autofunction:: get_scope
.. autofunction:: clear
.. autofunction:: remove
.. autofunction:: scroll_to

Content Outputting
-----------------------

.. _scope_param:

**Scope related parameters of output function**

The output function will output the content to the "current scope" by default, and the "current scope" for the runtime
context can be set by `use_scope()`.

In addition, all output functions support a ``scope`` parameter to specify the destination scope to output:

.. exportable-codeblock::
    :name: put-xxx-scope
    :summary: ``scope`` parameter of the output function

    with use_scope('scope3'):
        put_text('text1 in scope3')   # output to current scope: scope3
        put_text('text in ROOT scope', scope='ROOT')   # output to ROOT Scope

    put_text('text2 in scope3', scope='scope3')   # output to scope3

The results of the above code are as follows::

    text1 in scope3
    text2 in scope3
    text in ROOT scope

A scope can contain multiple output items, the default behavior of output function is to append its content to target scope.
The ``position`` parameter of output function can be used to specify the insert position in target scope.

Each output item in a scope has an index, the first item's index is 0, and the next item's index is incremented by one.
You can also use a negative number to index the items in the scope, -1 means the last item, -2 means the item before the last, ...

The ``position`` parameter of output functions accepts an integer. When ``position>=0``, it means to insert content
before the item whose index equal ``position``; when ``position<0``, it means to insert content after the item whose
index equal ``position``:

.. exportable-codeblock::
    :name: put-xxx-position
    :summary: `position` parameter of the output function

    with use_scope('scope1'):
        put_text('A')
    ## ----
    with use_scope('scope1'):  # ..demo-only
        put_text('B', position=0)   # insert B before A -> B A
    ## ----
    with use_scope('scope1'):  # ..demo-only
        put_text('C', position=-2)  # insert C after B -> B C A
    ## ----
    with use_scope('scope1'):  # ..demo-only
        put_text('D', position=1)   # insert D before C B -> B D C A

**Output functions**

.. autofunction:: put_text
.. autofunction:: put_markdown

.. py:function:: put_info(*contents, closable=False, scope=None, position=-1) -> Output:
                 put_success(*contents, closable=False, scope=None, position=-1) -> Output:
                 put_warning(*contents, closable=False, scope=None, position=-1) -> Output:
                 put_error(*contents, closable=False, scope=None, position=-1) -> Output:

    Output Messages.

    :param contents: Message contents.
       The item is ``put_xxx()`` call, and any other type will be converted to ``put_text(content)``.
    :param bool closable: Whether to show a dismiss button on the right of the message.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    .. versionadded:: 1.2

.. autofunction:: put_html
.. autofunction:: put_link
.. autofunction:: put_processbar
.. autofunction:: set_processbar
.. autofunction:: put_loading
.. autofunction:: put_code
.. autofunction:: put_table
.. autofunction:: span
.. autofunction:: put_buttons
.. autofunction:: put_button
.. autofunction:: put_image
.. autofunction:: put_file
.. autofunction:: put_tabs
.. autofunction:: put_collapse
.. autofunction:: put_scrollable
.. autofunction:: put_widget

Other Interactions
--------------------
.. autofunction:: toast
.. autofunction:: popup
.. autofunction:: close_popup

.. _style_and_layout:

Layout and Style
------------------
.. autofunction:: put_row
.. autofunction:: put_column
.. autofunction:: put_grid
.. autofunction:: style


"""
import copy
import html
import io
import logging
import string
from base64 import b64encode
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Union

from .io_ctrl import output_register_callback, send_msg, Output, safely_destruct_output_when_exp, OutputList, scope2dom
from .session import get_current_session, download
from .utils import random_str, iscoroutinefunction, check_dom_name_value

try:
    from PIL.Image import Image as PILImage
except ImportError:
    PILImage = type('MockPILImage', (), dict(__init__=None))

logger = logging.getLogger(__name__)

__all__ = ['Position', 'remove', 'scroll_to', 'put_tabs', 'put_scope',
           'put_text', 'put_html', 'put_code', 'put_markdown', 'use_scope', 'set_scope', 'clear', 'remove',
           'put_table', 'put_buttons', 'put_image', 'put_file', 'PopupSize', 'popup', 'put_button',
           'close_popup', 'put_widget', 'put_collapse', 'put_link', 'put_scrollable', 'style', 'put_column',
           'put_row', 'put_grid', 'span', 'put_processbar', 'set_processbar', 'put_loading',
           'output', 'toast', 'get_scope', 'put_info', 'put_error', 'put_warning', 'put_success']


# popup size
class PopupSize:
    LARGE = 'large'
    NORMAL = 'normal'
    SMALL = 'small'


class Position:
    TOP = 'top'
    MIDDLE = 'middle'
    BOTTOM = 'bottom'


# position value of `put_xxx()`
class OutputPosition:
    TOP = 0
    BOTTOM = -1


_scope_name_allowed_chars = set(string.ascii_letters + string.digits + '_-')


def set_scope(name, container_scope=None, position=OutputPosition.BOTTOM, if_exist=None):
    """Create a new scope.

    :param str name: scope name
    :param str container_scope: Specify the parent scope of this scope. 
        When the scope doesn't exist, no operation is performed.
    :param int position: The location where this scope is created in the parent scope.
       (see :ref:`Scope related parameters <scope_param>`)
    :param str if_exist: What to do when the specified scope already exists:

        - `None`: Do nothing
        - `'remove'`: Remove the old scope first and then create a new one
        - `'clear'`: Just clear the contents of the old scope, but don't create a new scope

       Default is `None`
    """
    if container_scope is None:
        container_scope = get_scope()
    check_dom_name_value(name, 'scope name')
    send_msg('output_ctl', dict(set_scope=scope2dom(name, no_css_selector=True),
                                container=scope2dom(container_scope),
                                position=position, if_exist=if_exist))


def get_scope(stack_idx=-1):
    """Get the scope name of runtime scope stack

    :param int stack_idx: The index of the runtime scope stack. Default is -1.

       0 means the top level scope(the ``ROOT`` Scope),
       -1 means the current Scope,
       -2 means the scope used before entering the current scope, ...
    :return: Returns the scope name with the index, and returns ``None`` when occurs index error
    """
    try:
        return get_current_session().get_scope_name(stack_idx)
    except IndexError:
        logger.exception("Scope stack index error")
        return None


def clear(scope=None):
    """Clear the content of the specified scope

    :param str scope: Target scope name. Default is the current scope.
    """
    if scope is None:
        scope = get_scope()
    send_msg('output_ctl', dict(clear=scope2dom(scope)))


def remove(scope=None):
    """Remove the specified scope

    :param str scope: Target scope name. Default is the current scope.
    """
    if scope is None:
        scope = get_scope()
    assert scope != 'ROOT', "Can not remove `ROOT` scope."
    send_msg('output_ctl', dict(remove=scope2dom(scope)))


def scroll_to(scope=None, position=Position.TOP):
    """
    Scroll the page to the specified scope

    :param str scope: Target scope. Default is the current scope.
    :param str position: Where to place the scope in the visible area of the page. Available value:

       * ``'top'`` : Keep the scope at the top of the visible area of the page
       * ``'middle'`` : Keep the scope at the middle of the visible area of the page
       * ``'bottom'`` : Keep the scope at the bottom of the visible area of the page
    """
    if scope is None:
        scope = get_scope()
    send_msg('output_ctl', dict(scroll_to=scope2dom(scope), position=position))


def _get_output_spec(type, scope, position, **other_spec):
    """
    get the spec dict of output functions

    :param str type: output type
    :param str scope: target scope
    :param int position:
    :param other_spec: Additional output parameters, the None value will not be included in the return value

    :return dict: ``spec`` field of ``output`` command
    """
    spec = dict(type=type)

    # add non-None arguments to spec
    spec.update({k: v for k, v in other_spec.items() if v is not None})

    if not scope:
        scope_name = get_scope()
    else:
        scope_name = scope

    spec['scope'] = scope2dom(scope_name)
    spec['position'] = position

    return spec


def put_text(*texts, sep=' ', inline=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """
    Output plain text

    :param texts: Texts need to output. The type can be any object, and the `str()` function will be used for non-string objects.
    :param str sep: The separator between the texts
    :param bool inline: Use text as an inline element (no line break at the end of the text). Default is ``False``
    :param str scope: The target scope to output. If the scope does not exist, no operation will be performed.

       Can specify the scope name or use a integer to index the runtime scope stack.
    :param int position: The position where the content is output in target scope

    For more information about ``scope`` and ``position`` parameter, please refer to :ref:`User Manual <scope_param>`
    """
    content = sep.join(str(i) for i in texts)
    spec = _get_output_spec('text', content=content, inline=inline, scope=scope, position=position)
    return Output(spec)


def _put_message(color, contents, closable=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    tpl = r"""
<div class="alert alert-{{color}} {{#dismissible}}alert-dismissible fade show{{/dismissible}}" role="alert">
{{#contents}}
    {{& pywebio_output_parse}}
{{/contents}}
{{#dismissible}}
<button type="button" class="close" data-dismiss="alert" aria-label="Close">
<span aria-hidden="true">&times;</span>
</button>
{{/dismissible}}
</div>""".strip()
    contents = [c if isinstance(c, Output) else put_text(c) for c in contents]
    return put_widget(template=tpl, data=dict(color=color, contents=contents, dismissible=closable),
                      scope=scope, position=position).enable_context_manager()


def put_info(*contents, closable=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output information message.

    :param contents: Message contents.
       The item is ``put_xxx()`` call, and any other type will be converted to ``put_text(content)``.
    :param bool closable: Whether to show a dismiss button on the right of the message.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    .. versionadded:: 1.2
    """
    return _put_message(color='info', contents=contents, closable=closable, scope=scope, position=position)


def put_success(*contents, closable=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output success message.
    .. seealso:: `put_info()`
    .. versionadded:: 1.2
    """
    return _put_message(color='success', contents=contents, closable=closable, scope=scope, position=position)


def put_warning(*contents, closable=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output warning message.
    .. seealso:: `put_info()`
    """
    return _put_message(color='warning', contents=contents, closable=closable, scope=scope, position=position)


def put_error(*contents, closable=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output error message.
    .. seealso:: `put_info()`
    """
    return _put_message(color='danger', contents=contents, closable=closable, scope=scope, position=position)


def put_html(html, sanitize=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """
    Output HTML content

    :param html: html string
    :param bool sanitize: Whether to use `DOMPurify <https://github.com/cure53/DOMPurify>`_ to filter the content to prevent XSS attacks.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`
    """

    # Compatible with ipython rich output
    # See: https://ipython.readthedocs.io/en/stable/config/integrating.html?highlight=Rich%20display#rich-display
    if hasattr(html, '__html__'):
        html = html.__html__()
    elif hasattr(html, '_repr_html_'):
        html = html._repr_html_()

    spec = _get_output_spec('html', content=html, sanitize=sanitize, scope=scope, position=position)
    return Output(spec)


def put_code(content, language='', rows=None, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """
    Output code block

    :param str content: code string
    :param str language: language of code
    :param int rows: The max lines of code can be displayed, no limit by default. The scroll bar will be displayed when the content exceeds.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`
    """
    if not isinstance(content, str):
        content = str(content)

    # For fenced code blocks, escaping the backtick need to use more backticks
    backticks = '```'
    while backticks in content:
        backticks += '`'

    code = "%s%s\n%s\n%s" % (backticks, language, content, backticks)
    out = put_markdown(code, scope=scope, position=position)
    if rows is not None:
        max_height = rows * 19 + 32  # 32 is the code css padding
        out.style("max-height: %spx" % max_height)
    return out


def _left_strip_multiple_line_string_literal(s):
    """Remove the indent for code format in string literal

    * The first line may have no leading whitespace
    * There may be empty line in s (since PyCharm will remove the line trailing whitespace)
    """
    lines = s.splitlines()
    if len(lines) < 2:
        return s

    line = ''
    for line in lines[1:]:
        if line:
            break

    strip_cnt = 1
    while line[:strip_cnt] in (' ' * strip_cnt, '\t' * strip_cnt):
        strip_cnt += 1

    for line in lines[1:]:
        while line.strip() and line[:strip_cnt] not in (' ' * strip_cnt, '\t' * strip_cnt):
            strip_cnt -= 1

    lines_ = [i[strip_cnt:] for i in lines[1:]]
    return '\n'.join(lines[:1] + lines_)


def put_markdown(mdcontent, lstrip=True, options=None, sanitize=True,
                 scope=None, position=OutputPosition.BOTTOM, **kwargs) -> Output:
    """
    Output Markdown

    :param str mdcontent: Markdown string
    :param bool lstrip: Whether to remove the leading whitespace in each line of ``mdcontent``.
        The number of the whitespace to remove will be decided cleverly.
    :param dict options: Configuration when parsing Markdown.
       PyWebIO uses `marked <https://marked.js.org/>`_ library to parse Markdown,
       the parse options see: https://marked.js.org/using_advanced#options (Only supports members of string and boolean type)
    :param bool sanitize: Whether to use `DOMPurify <https://github.com/cure53/DOMPurify>`_ to filter the content to prevent XSS attacks.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    When using Python triple quotes syntax to output multi-line Markdown in a function,
    you can indent the Markdown text to keep a good code format.
    PyWebIO will cleverly remove the indent for you when show the Markdown::

        # good code format
        def hello():
            put_markdown(r\""" # H1
            This is content.
            \""")

    .. versionchanged:: 1.5
       Enable `lstrip` by default.
       Deprecate `strip_indent`.
    """
    if 'strip_indent' in kwargs:
        import warnings
        # use stacklevel=2 to make the warning refer to put_markdown() call
        warnings.warn("`strip_indent` parameter is deprecated in `put_markdown()`", DeprecationWarning, stacklevel=2)

    if lstrip:
        mdcontent = _left_strip_multiple_line_string_literal(mdcontent)

    spec = _get_output_spec('markdown', content=mdcontent, options=options, sanitize=sanitize,
                            scope=scope, position=position)
    return Output(spec)


class span_:
    def __init__(self, content, row=1, col=1):
        self.content, self.row, self.col = content, row, col


@safely_destruct_output_when_exp('content')
def span(content, row=1, col=1):
    """Create cross-cell content in :func:`put_table()` and :func:`put_grid()`

    :param content: cell content. It can be a string or ``put_xxx()`` call.
    :param int row: Vertical span, that is, the number of spanning rows
    :param int col: Horizontal span, that is, the number of spanning columns

    :Example:

    .. exportable-codeblock::
        :name: span
        :summary: Create cross-cell content with `span()`

        put_table([
            ['C'],
            [span('E', col=2)],  # 'E' across 2 columns
        ], header=[span('A', row=2), 'B'])  # 'A' across 2 rows

        put_grid([
            [put_text('A'), put_text('B')],
            [span(put_text('A'), col=2)],  # 'A' across 2 columns
        ])

    """
    return span_(content, row, col)


@safely_destruct_output_when_exp('tdata')
def put_table(tdata, header=None, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """
    Output table

    :param list tdata: Table data, which can be a two-dimensional list or a list of dict.
       The table cell can be a string or ``put_xxx()`` call. The cell can use the :func:`span()` to set the cell span.
    :param list header: Table header.
       When the item of ``tdata`` is of type ``list``, if the ``header`` parameter is omitted,
       the first item of ``tdata`` will be used as the header.
       The header item can also use the :func:`span()` function to set the cell span.

       When ``tdata`` is list of dict, ``header`` is used to specify the order of table headers, which cannot be omitted.
       In this case, the ``header`` can be a list of dict key or a list of ``(<label>, <dict key>)``.

    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    Example:

    .. exportable-codeblock::
        :name: put_table
        :summary: Output table with `put_table()`

        # 'Name' cell across 2 rows, 'Address' cell across 2 columns
        put_table([
            [span('Name',row=2), span('Address', col=2)],
            ['City', 'Country'],
            ['Wang', 'Beijing', 'China'],
            ['Liu', 'New York', 'America'],
        ])
        ## ----

        # Use `put_xxx()` in `put_table()`
        put_table([
            ['Type', 'Content'],
            ['html', put_html('X<sup>2</sup>')],
            ['text', '<hr/>'],
            ['buttons', put_buttons(['A', 'B'], onclick=...)],  # ..doc-only
            ['buttons', put_buttons(['A', 'B'], onclick=put_text)],  # ..demo-only
            ['markdown', put_markdown('`Awesome PyWebIO!`')],
            ['file', put_file('hello.text', b'hello world')],
            ['table', put_table([['A', 'B'], ['C', 'D']])]
        ])
        ## ----

        # Set table header
        put_table([
            ['Wang', 'M', 'China'],
            ['Liu', 'W', 'America'],
        ], header=['Name', 'Gender', 'Address'])
        ## ----

        # When ``tdata`` is list of dict
        put_table([
            {"Course":"OS", "Score": "80"},
            {"Course":"DB", "Score": "93"},
        ], header=["Course", "Score"])  # or header=[(put_markdown("*Course*"), "Course"), (put_markdown("*Score*") ,"Score")]

    .. versionadded:: 0.3
       The cell of table support ``put_xxx()`` calls.
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
    Format `buttons` parameter in `put_buttons()`, replace its value with its idx
    :param buttons:
        {label:, value:, }
        (label, value, )
        single value, label=value

    :return: [{value:, label:, }, ...], values
    """

    btns = []
    values = []
    for idx, btn in enumerate(buttons):
        btn = copy.deepcopy(btn)
        if isinstance(btn, Mapping):
            assert 'value' in btn and 'label' in btn, 'actions item must have value and label key'
        elif isinstance(btn, (list, tuple)):
            assert len(btn) == 2, 'actions item format error'
            btn = dict(zip(('label', 'value'), btn))
        else:
            btn = dict(value=btn, label=btn)
        values.append(btn['value'])
        btn['value'] = idx
        btns.append(btn)
    return btns, values


def put_buttons(buttons, onclick, small=None, link_style=False, outline=False, group=False, scope=None,
                position=OutputPosition.BOTTOM, **callback_options) -> Output:
    """
    Output a group of buttons and bind click event

    :param list buttons: Button list. The available formats of list items are:

        * dict::

            {
                "label":(str)button label,
                "value":(str)button value,
                "color":(str, optional)button color,
                "disabled":(bool, optional) whether the button is disabled
            }

        * tuple or list: ``(label, value)``
        * single value: label and value of option use the same value

        The ``value`` of button can be any type.
        The ``color`` of button can be one of: `primary`, `secondary`, `success`, `danger`, `warning`, `info`, `light`, `dark`.

        Example:

        .. exportable-codeblock::
            :name: put_buttons-btn_class
            :summary: `put_buttons()`

            put_buttons([dict(label='success', value='s', color='success')], onclick=...)  # ..doc-only
            put_buttons([  # ..demo-only
                dict(label=i, value=i, color=i)  # ..demo-only
                for i in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']  # ..demo-only
            ], onclick=put_text)  # ..demo-only

    :type onclick: callable / list
    :param onclick: Callback which will be called when button is clicked. ``onclick`` can be a callable object or a list of it.

       If ``onclick`` is callable object, its signature is ``onclick(btn_value)``. ``btn_value`` is ``value`` of the button that is clicked.

       If ``onclick`` is a list, the item receives no parameter. In this case, each item in the list corresponds to the buttons one-to-one.

       Tip: You can use ``functools.partial`` to save more context information in ``onclick``.

       Note: When in :ref:`Coroutine-based session  <coroutine_based_session>`, the callback can be a coroutine function.
    :param bool small: Whether to use small size button. Default is False.
    :param bool link_style: Whether to use link style button. Default is False
    :param bool outline: Whether to use outline style button. Default is False
    :param bool group: Whether to group the buttons together. Default is False
    :param int scope, position: Those arguments have the same meaning as for `put_text()`
    :param callback_options: Other options of the ``onclick`` callback. There are different options according to the session implementation

       When in Coroutine-based Session:
           * mutex_mode: Default is ``False``. If set to ``True``, new click event will be ignored when the current callback is running.
             This option is available only when ``onclick`` is a coroutine function.

       When in Thread-based Session:
           * serial_mode: Default is ``False``, and every time a callback is triggered,
             the callback function will be executed immediately in a new thread.

           If set ``serial_mode`` to ``True``
           After enabling serial_mode, the button's callback will be executed serially in a resident thread in the session,
           and all other new click event callbacks (including the ``serial_mode=False`` callback) will be queued for
           the current click event to complete. If the callback function runs for a short time,
           you can turn on ``serial_mode`` to improve performance.

    Example:

    .. exportable-codeblock::
        :name: put_buttons
        :summary: `put_buttons()` usage

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

    .. versionchanged:: 1.5
       Add ``disabled`` button support.
       The ``value`` of button can be any object.
    """
    btns, values = _format_button(buttons)

    if isinstance(onclick, Sequence):
        assert len(btns) == len(onclick), "`onclick` and `buttons` must be same length."

    def click_callback(btn_idx):
        if isinstance(onclick, Sequence):
            return onclick[btn_idx]()
        else:
            btn_val = values[btn_idx]
            if not btns[btn_idx].get('disabled'):
                return onclick(btn_val)

    callback_id = output_register_callback(click_callback, **callback_options)
    spec = _get_output_spec('buttons', callback_id=callback_id, buttons=btns, small=small,
                            scope=scope, position=position, link=link_style, outline=outline, group=group)

    return Output(spec)


def put_button(label, onclick, color=None, small=None, link_style=False, outline=False, disabled=False, scope=None,
               position=OutputPosition.BOTTOM) -> Output:
    """Output a single button and bind click event to it.

    :param str label: Button label
    :param callable onclick: Callback which will be called when button is clicked.
    :param str color: The color of the button,
        can be one of: `primary`, `secondary`, `success`, `danger`, `warning`, `info`, `light`, `dark`.
    :param bool disabled: Whether the button is disabled
    :param - small, link_style, outline, scope, position:  Those arguments have the same meaning as for `put_buttons()`

    Example:

    .. exportable-codeblock::
        :name: put_button
        :summary: `put_button()` usage

        put_button("click me", onclick=lambda: toast("Clicked"), color='success', outline=True)

    .. versionadded:: 1.4

    .. versionchanged:: 1.5
       add ``disabled`` parameter
    """
    return put_buttons([{'label': label, 'value': '', 'color': color or 'primary', 'disabled': disabled}],
                       onclick=[onclick], small=small, link_style=link_style, outline=outline, scope=scope,
                       position=position)


def put_image(src, format=None, title='', width=None, height=None,
              scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output image

    :param src: Source of image. It can be a string specifying image URL, a bytes-like object specifying
        the binary content of an image or an instance of ``PIL.Image.Image``
    :param str title: Image description.
    :param str width: The width of image. It can be CSS pixels (like `'30px'`) or percentage (like `'10%'`).
    :param str height: The height of image. It can be CSS pixels (like `'30px'`) or percentage (like `'10%'`).
       If only one value of ``width`` and ``height`` is specified, the browser will scale image according to its original size.
    :param str format: Image format, optinoal. e.g.: ``png``, ``jpeg``, ``gif``, etc. Only available when `src` is non-URL
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    Example:

    .. exportable-codeblock::
        :name: put_image
        :summary: `put_image()` usage

        from pywebio import STATIC_PATH  # ..demo-only
        img = open(STATIC_PATH + '/image/favicon_open_32.png', 'rb').read()  # ..demo-only
        img = open('/path/to/some/image.png', 'rb').read()  # ..doc-only
        put_image(img, width='50px')

        ## ----
        put_image('https://www.python.org/static/img/python-logo.png')
    """
    if isinstance(src, PILImage):
        format = format or src.format or 'JPEG'
        imgByteArr = io.BytesIO()
        src.save(imgByteArr, format=format)
        src = imgByteArr.getvalue()

    if isinstance(src, (bytes, bytearray)):
        b64content = b64encode(src).decode('ascii')
        format = '' if format is None else ('image/%s' % format)
        format = html.escape(format, quote=True)
        src = "data:{format};base64, {b64content}".format(format=format, b64content=b64content)

    width = 'width="%s"' % html.escape(width, quote=True) if width is not None else ''
    height = 'height="%s"' % html.escape(height, quote=True) if height is not None else ''

    tag = r'<img src="{src}" alt="{title}" {width} {height}/>'.format(src=src, title=html.escape(title, quote=True),
                                                                      height=height, width=width)
    return put_html(tag, scope=scope, position=position)


def put_file(name, content, label=None, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a link to download a file

    To show a link with the file name on the browser. When click the link, the browser automatically downloads the file.

    :param str name: File name downloaded as
    :param content: File content. It is a bytes-like object
    :param str label: The label of the download link, which is the same as the file name by default.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    Example:

    .. exportable-codeblock::
        :name: put_file
        :summary: `put_file()` usage

        content = open('./some-file', 'rb').read()  # ..doc-only
        content = open('README.md', 'rb').read()    # ..demo-only
        put_file('hello-world.txt', content, 'download me')
    """
    if label is None:
        label = name
    output = put_buttons(buttons=[label], link_style=True,
                         onclick=[lambda: download(name, content)],
                         scope=scope, position=position)
    return output


def put_link(name, url=None, app=None, new_window=False, scope=None,
             position=OutputPosition.BOTTOM) -> Output:
    """Output hyperlinks to other web page or PyWebIO Application page.

    :param str name: The label of the link
    :param str url: Target url
    :param str app: Target PyWebIO Application name. See also: :ref:`Server mode <server_and_script_mode>`
    :param bool new_window: Whether to open the link in a new window
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    The ``url`` and ``app`` parameters must specify one but not both
    """
    assert bool(url is None) != bool(app is None), "Must set `url` or `app` parameter but not both"

    href = 'javascript:WebIO.openApp(%r, %d)' % (app, new_window) if app is not None else url
    target = '_blank' if (new_window and url) else '_self'
    tag = '<a href="{href}" target="{target}">{name}</a>'.format(
        href=html.escape(href, quote=True), target=target, name=html.escape(name))
    return put_html(tag, scope=scope, position=position)


def put_processbar(name, init=0, label=None, auto_close=False, scope=None,
                   position=OutputPosition.BOTTOM) -> Output:
    """Output a process bar

    :param str name: The name of the progress bar, which is the unique identifier of the progress bar
    :param float init: The initial progress value of the progress bar. The value is between 0 and 1
    :param str label: The label of process bar. The default is the percentage value of the current progress.
    :param bool auto_close: Whether to remove the progress bar after the progress is completed
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    Example:

    .. exportable-codeblock::
        :name: put_processbar
        :summary: `put_processbar()` usage

        import time

        put_processbar('bar');
        for i in range(1, 11):
            set_processbar('bar', i / 10)
            time.sleep(0.1)

    .. seealso:: use `set_processbar()` to set the progress of progress bar
    """
    check_dom_name_value(name)
    processbar_id = 'webio-processbar-%s' % name
    percentage = init * 100
    label = '%.1f%%' % percentage if label is None else label
    tpl = """<div class="progress" style="margin-top: 4px;">
                <div id="{{elem_id}}" class="progress-bar bg-info progress-bar-striped progress-bar-animated" role="progressbar"
                     style="width: {{percentage}}%;" aria-valuenow="{{init}}" aria-valuemin="0" aria-valuemax="1" data-auto-close="{{auto_close}}">{{label}}
                </div>
            </div>"""
    return put_widget(tpl, data=dict(elem_id=processbar_id, init=init, label=label,
                                     percentage=percentage, auto_close=int(bool(auto_close))), scope=scope,
                      position=position)


def set_processbar(name, value, label=None):
    """Set the progress of progress bar

    :param str name: The name of the progress bar
    :param float value: The progress value of the progress bar. The value is between 0 and 1
    :param str label: The label of process bar. The default is the percentage value of the current progress.

    See also: `put_processbar()`
    """
    from pywebio.session import run_js

    check_dom_name_value(name)

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


def put_loading(shape='border', color='dark', scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output loading prompt

    :param str shape: The shape of loading prompt. The available values are: `'border'` (default)、 `'grow'`
    :param str color: The color of loading prompt. The available values are: `'primary'` 、 `'secondary'` 、
        `'success'` 、 `'danger'` 、 `'warning'` 、`'info'`  、`'light'`  、 `'dark'` (default)
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    `put_loading()` can be used in 2 ways: direct call and context manager:

    .. exportable-codeblock::
        :name: put_loading
        :summary: `put_loading()` usage

        for shape in ('border', 'grow'):
            for color in ('primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark'):
                put_text(shape, color)
                put_loading(shape=shape, color=color)

        ## ----
        import time  # ..demo-only
        # Use as context manager, the loading prompt will disappear automatically when the context block exits.
        with put_loading():
            time.sleep(3)  # Some time-consuming operations
            put_text("The answer of the universe is 42")

        ## ----
        # using style() to set the size of the loading prompt
        put_loading().style('width:4rem; height:4rem')
    """
    assert shape in ('border', 'grow'), "shape must in ('border', 'grow')"
    assert color in {'primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark'}

    html = """<div class="spinner-{shape} text-{color}" role="status">
                <span class="sr-only">Loading...</span>
            </div>""".format(shape=shape, color=color)

    scope_name = random_str(10)

    def enter(self):
        self.spec['container_dom_id'] = scope2dom(scope_name, no_css_selector=True)
        self.send()
        return scope_name

    def exit_(self, exc_type, exc_val, exc_tb):
        remove(scope_name)
        return False  # Propagate Exception

    return put_html(html, sanitize=False, scope=scope, position=position). \
        enable_context_manager(custom_enter=enter, custom_exit=exit_)


@safely_destruct_output_when_exp('content')
def put_collapse(title, content=[], open=False, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output collapsible content

    :param str title: Title of content
    :type content: list/str/put_xxx()
    :param content: The content can be a string, the ``put_xxx()`` calls , or a list of them.
    :param bool open: Whether to expand the content. Default is ``False``.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    Example:

    .. exportable-codeblock::
        :name: put_collapse
        :summary: `put_collapse()` usage

        put_collapse('Collapse title', [
            'text',
            put_markdown('~~Strikethrough~~'),
            put_table([
                ['Commodity', 'Price'],
                ['Apple', '5.5'],
            ])
        ], open=True)

        ## ----
        put_collapse('Large text', 'Awesome PyWebIO! '*30)
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
    return put_widget(tpl, dict(title=title, contents=content, open=open), scope=scope,
                      position=position).enable_context_manager()


@safely_destruct_output_when_exp('content')
def put_scrollable(content=[], height=400, keep_bottom=False, border=True,
                   scope=None, position=OutputPosition.BOTTOM, **kwargs) -> Output:
    """Output a fixed height content area. scroll bar is displayed when the content exceeds the limit

    :type content: list/str/put_xxx()
    :param content: The content can be a string, the ``put_xxx()`` calls , or a list of them.
    :param int/tuple height: The height of the area (in pixels).
       ``height`` parameter also accepts ``(min_height, max_height)`` to indicate the range of height, for example,
       ``(100, 200)`` means that the area has a minimum height of 100 pixels and a maximum of 200 pixels.
       Set ``None`` if you don't want to limit the height
    :param bool keep_bottom: Whether to keep the content area scrolled to the bottom when updated.
    :param bool border: Whether to show border
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    Example:

    .. exportable-codeblock::
        :name: put_scrollable
        :summary: `put_scrollable()` usage

        import time

        put_scrollable(put_scope('scrollable'), height=200, keep_bottom=True)
        put_text("You can click the area to prevent auto scroll.", scope='scrollable')

        while 1:
            put_text(time.time(), scope='scrollable')
            time.sleep(0.5)

    .. versionchanged:: 1.1
       add ``height`` parameter，remove ``max_height`` parameter；
       add ``keep_bottom`` parameter

    .. versionchanged:: 1.5
       remove ``horizon_scroll`` parameter
    """
    if not isinstance(content, (list, tuple, OutputList)):
        content = [content]

    content = [i if isinstance(i, Output) else put_text(i) for i in content]

    if 'max_height' in kwargs:
        import warnings
        # use stacklevel=2 to make the warning refer to the put_scrollable() call
        warnings.warn("`max_height` parameter is deprecated in `put_scrollable()`, use `height` instead.",
                      DeprecationWarning, stacklevel=2)
        height = kwargs['max_height']  # Backward compatible

    try:
        min_height, max_height = height
    except Exception:
        min_height, max_height = height, height

    spec = _get_output_spec('scrollable', contents=content, min_height=min_height, max_height=max_height,
                            keep_bottom=keep_bottom, border=border, scope=scope, position=position)
    return Output(spec).enable_context_manager(container_selector='> div')


@safely_destruct_output_when_exp('tabs')
def put_tabs(tabs, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output tabs.

    :param list tabs: Tab list, each item is a dict: ``{"title": "Title", "content": ...}`` .
       The ``content`` can be a string, the ``put_xxx()`` calls , or a list of them.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    .. exportable-codeblock::
        :name: put_tabs
        :summary: `put_tabs()` usage

        put_tabs([
            {'title': 'Text', 'content': 'Hello world'},
            {'title': 'Markdown', 'content': put_markdown('~~Strikethrough~~')},
            {'title': 'More content', 'content': [
                put_table([
                    ['Commodity', 'Price'],
                    ['Apple', '5.5'],
                    ['Banana', '7'],
                ]),
                put_link('pywebio', 'https://github.com/wang0618/PyWebIO')
            ]},
        ])

    .. versionadded:: 1.3
    """

    for tab in tabs:
        assert 'title' in tab and 'content' in tab

    spec = _get_output_spec('tabs', tabs=tabs, scope=scope, position=position)
    return Output(spec)


@safely_destruct_output_when_exp('data')
def put_widget(template, data, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output your own widget

    :param template: html template, using `mustache.js <https://github.com/janl/mustache.js>`_ syntax
    :param dict data: Data used to render the template.

       The data can include the ``put_xxx()`` calls, and the JS function ``pywebio_output_parse`` can be used to
       parse the content of ``put_xxx()``. For string input, ``pywebio_output_parse`` will parse into text.

       ⚠️：When using the ``pywebio_output_parse`` function, you need to turn off the html escaping of mustache:
       ``{{& pywebio_output_parse}}``, see the example below.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    :Example:

    .. exportable-codeblock::
        :name: put_widget
        :summary: Use `put_widget()` to output your own widget

        tpl = '''
        <details {{#open}}open{{/open}}>
            <summary>{{title}}</summary>
            {{#contents}}
                {{& pywebio_output_parse}}
            {{/contents}}
        </details>
        '''

        put_widget(tpl, {
            "open": True,
            "title": 'More content',
            "contents": [
                'text',
                put_markdown('~~Strikethrough~~'),
                put_table([
                    ['Commodity', 'Price'],
                    ['Apple', '5.5'],
                    ['Banana', '7'],
                ])
            ]
        })
    """
    spec = _get_output_spec('custom_widget', template=template, data=data, scope=scope, position=position)
    return Output(spec)


@safely_destruct_output_when_exp('content')
def put_row(content=[], size=None, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Use row layout to output content. The content is arranged horizontally

    :param list content: Content list, the item is ``put_xxx()`` call or ``None``. ``None`` represents the space between the output
    :param str size:
       | Used to indicate the width of the items, is a list of width values separated by space.
       | Each width value corresponds to the items one-to-one. (``None`` item should also correspond to a width value).
       | By default, ``size`` assigns a width of 10 pixels to the ``None`` item, and distributes the width equally to the remaining items.

       Available format of width value are:

        - pixels: like ``100px``
        - percentage: Indicates the percentage of available width. like ``33.33%``
        - ``fr`` keyword: Represents a scale relationship, 2fr represents twice the width of 1fr
        - ``auto`` keyword: Indicates that the length is determined by the browser
        - ``minmax(min, max)`` : Generate a length range, indicating that the length is within this range.
          It accepts two parameters, minimum and maximum.
          For example: ``minmax(100px, 1fr)`` means the length is not less than 100px and not more than 1fr

    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    :Example:

    .. exportable-codeblock::
        :name: put_row
        :summary: `put_row()` usage

        # Two code blocks of equal width, separated by 10 pixels
        put_row([put_code('A'), None, put_code('B')])
        ## ----

        # The width ratio of the left and right code blocks is 2:3, which is equivalent to size='2fr 10px 3fr'
        put_row([put_code('A'), None, put_code('B')], size='40% 10px 60%')

    """
    return _row_column_layout(content, flow='column', size=size, scope=scope,
                              position=position).enable_context_manager()


@safely_destruct_output_when_exp('content')
def put_column(content=[], size=None, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Use column layout to output content. The content is arranged vertically

    :param list content: Content list, the item is ``put_xxx()`` call or ``None``. ``None`` represents the space between the output
    :param str size: Used to indicate the width of the items, is a list of width values separated by space.
        The format is the same as the ``size`` parameter of the `put_row()` function.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`
    """

    return _row_column_layout(content, flow='row', size=size, scope=scope, position=position).enable_context_manager()


def _row_column_layout(content, flow, size, scope=None, position=OutputPosition.BOTTOM) -> Output:
    if not isinstance(content, (list, tuple, OutputList)):
        content = [content]

    if not size:
        size = ' '.join('1fr' if c is not None else '10px' for c in content)

    content = [c if c is not None else put_html('<div></div>') for c in content]
    for item in content:
        assert isinstance(item, Output), "put_row()/put_column()'s content must be list of put_xxx()"

    style = 'grid-auto-flow: {flow}; grid-template-{flow}s: {size};'.format(flow=flow, size=size)
    tpl = """
    <div style="display: grid; %s">
        {{#contents}}
            {{& pywebio_output_parse}}
        {{/contents}}
    </div>""".strip() % html.escape(style, quote=True)
    return put_widget(template=tpl, data=dict(contents=content), scope=scope,
                      position=position)


@safely_destruct_output_when_exp('content')
def put_grid(content, cell_width='auto', cell_height='auto', cell_widths=None, cell_heights=None, direction='row',
             scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output content using grid layout

    :param content: Content of grid, which is a two-dimensional list. The item of list is ``put_xxx()`` call or ``None``.
       ``None`` represents the space between the output. The item can use the `span()` to set the cell span.
    :param str cell_width: The width of grid cell.
    :param str cell_height: The height of grid cell.
    :param str cell_widths: The width of each column of the grid. The width values are separated by a space.
       Can not use ``cell_widths`` and ``cell_width`` at the same time
    :param str cell_heights: The height of each row of the grid. The height values are separated by a space.
       Can not use ``cell_heights`` and ``cell_height`` at the same time
    :param str direction: Controls how auto-placed items get inserted in the grid.
       Can be ``'row'``(default) or ``'column'`` .

        | ``'row'`` : Places items by filling each row
        | ``'column'`` : Places items by filling each column

    :param int scope, position: Those arguments have the same meaning as for `put_text()`

    The format of width/height value in ``cell_width``,``cell_height``,``cell_widths``,``cell_heights``
    can refer to the ``size`` parameter of the `put_row()` function.

    :Example:

    .. exportable-codeblock::
        :name: put_grid
        :summary: `put_grid()` usage

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
                for i in range(cell.row):
                    lens[x + i] += cell.col

                css = 'grid-row-start: span {row}; grid-column-start: span {col};'.format(row=cell.row, col=cell.col)
                elem = put_html('<div></div>') if cell.content is None else cell.content
                content[x][y] = elem.style(css)
            else:
                lens[x] += 1

            if content[x][y] is None:
                content[x][y] = put_html('<div></div>')

    # 为长度不足的行添加空元素
    # Add empty elements for rows with insufficient length
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
    </div>""".strip() % html.escape(css, quote=True)
    return put_widget(template=tpl, data=dict(contents=content), scope=scope, position=position)


@safely_destruct_output_when_exp('content')
def put_scope(name, content=[], scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a scope

    :param str name:
    :param list/put_xxx() content: The initial content of the scope, can be ``put_xxx()`` or a list of it.
    :param int scope, position: Those arguments have the same meaning as for `put_text()`
    """
    if not isinstance(content, list):
        content = [content]

    check_dom_name_value(name, 'scope name')
    dom_id = scope2dom(name, no_css_selector=True)

    spec = _get_output_spec('scope', dom_id=dom_id, contents=content, scope=scope, position=position)
    return Output(spec)


@safely_destruct_output_when_exp('contents')
def output(*contents):
    """Placeholder of output

    .. deprecated:: 1.5
        See :ref:`User Guide <put_scope>` for new way to set css style for output.

     ``output()`` can be passed in anywhere that ``put_xxx()`` can passed in. A handler it returned by ``output()``,
     and after being output, the content can also be modified by the handler (See code example below).

    :param contents: The initial contents to be output.
       The item is ``put_xxx()`` call, and any other type will be converted to ``put_text(content)``.
    :return: An OutputHandler instance, the methods of the instance are as follows:

    * ``reset(*contents)`` : Reset original contents to ``contents``
    * ``append(*contents)`` : Append ``contents`` to original contents
    * ``insert(idx, *contents)`` : insert ``contents`` into original contents.

       | when idx>=0, the output content is inserted before the element of the ``idx`` index.
       | when idx<0, the output content is inserted after the element of the ``idx`` index.

    Among them, the parameter ``contents`` is the same as ``output()``.

    :Example:

    .. exportable-codeblock::
        :name: output
        :summary: `output()` usage

        hobby = output(put_text('Coding'))  # equal to output('Coding')
        put_table([
           ['Name', 'Hobbies'],
           ['Wang', hobby]      # hobby is initialized to Coding
        ])
        ## ----

        hobby.reset('Movie')  # hobby is reset to Movie
        ## ----
        hobby.append('Music', put_text('Drama'))  # append Music, Drama to hobby
        ## ----
        hobby.insert(0, put_markdown('**Coding**'))  # insert the Coding into the top of the hobby

    """

    import warnings
    # use stacklevel=2 to make the warning refer to the output() call
    warnings.warn("`pywebio.output.output()` is deprecated since v1.5 and will remove in the future version, "
                  "use `pywebio.output.put_scope()` instead", DeprecationWarning, stacklevel=2)

    class OutputHandler(Output):
        """
        与 `Output` 的不同在于， 不会在销毁时(__del__)自动输出
        The difference with `Output` is that `OutputHandler` will not automatically output when destroyed (__del__)
        """

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
                if not isinstance(o, Output):
                    o = put_text(o)
                o.spec['scope'] = scope2dom(self.scope)
                o.spec['position'] = OutputPosition.BOTTOM
                o.send()

        @safely_destruct_output_when_exp('outputs')
        def insert(self, idx, *outputs):
            """
            idx可为负
            idx can be negative
            """
            direction = 1 if idx >= 0 else -1
            for acc, o in enumerate(outputs):
                if not isinstance(o, Output):
                    o = put_text(o)
                o.spec['scope'] = scope2dom(self.scope)
                o.spec['position'] = idx + direction * acc
                o.send()

    contents = [c if isinstance(c, Output) else put_text(c) for c in contents]

    dom_name = random_str(10)
    tpl = """<div class="{{dom_class_name}}">
            {{#contents}}
                {{#.}}
                    {{& pywebio_output_parse}}
                {{/.}}
            {{/contents}}
        </div>"""
    out_spec = put_widget(template=tpl,
                          data=dict(contents=contents, dom_class_name=scope2dom(dom_name, no_css_selector=True)))
    return OutputHandler(Output.dump_dict(out_spec), ('.', dom_name))


@safely_destruct_output_when_exp('outputs')
def style(outputs, css_style) -> Union[Output, OutputList]:
    """Customize the css style of output content

    .. deprecated:: 1.3
        See :ref:`User Guide <style>` for new way to set css style for output.

    :param outputs: The output content can be a ``put_xxx()`` call or a list of it.
    :type outputs: list/put_xxx()
    :param str css_style: css style string
    :return: The output contents with css style added:

       Note: If ``outputs`` is a list of ``put_xxx()`` calls, the style will be set for each item of the list.
       And the return value can be used in anywhere accept a list of ``put_xxx()`` calls.

    :Example:

    .. exportable-codeblock::
        :name: style-deprecated
        :summary: `style()` usage

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
    import warnings
    warnings.warn("`pywebio.output.style()` is deprecated since v1.3 and will remove in the future version, "
                  "use `put_xxx(...).style(...)` instead", DeprecationWarning, stacklevel=2)

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
    """
    Show a popup.

    ⚠️: In PyWebIO, you can't show multiple popup windows at the same time. Before displaying a new pop-up window,
    the existing popup on the page will be automatically closed. You can use `close_popup()` to close the popup manually.

    :param str title: The title of the popup.
    :type content: list/str/put_xxx()
    :param content: The content of the popup can be a string, the put_xxx() calls , or a list of them.
    :param str size: The size of popup window. Available values are: ``'large'``, ``'normal'`` and ``'small'``.
    :param bool implicit_close: If enabled, the popup can be closed implicitly by clicking the content outside
        the popup window or pressing the ``Esc`` key. Default is ``False``.
    :param bool closable: Whether the user can close the popup window. By default, the user can close the popup
        by clicking the close button in the upper right of the popup window.
        When set to ``False``, the popup window can only be closed by :func:`popup_close()`,
        at this time the ``implicit_close`` parameter will be ignored.

    ``popup()`` can be used in 3 ways: direct call, context manager, and decorator.

    * direct call:

    .. exportable-codeblock::
        :name: popup
        :summary: `popup()` usage

        popup('popup title', 'popup text content', size=PopupSize.SMALL)
        ## ----

        popup('Popup title', [
            put_html('<h3>Popup Content</h3>'),
            'html: <br/>',
            put_table([['A', 'B'], ['C', 'D']]),
            put_buttons(['close_popup()'], onclick=lambda _: close_popup())
        ])

    * context manager:

    .. exportable-codeblock::
        :name: popup-context
        :summary: `popup()` as context manager

        with popup('Popup title') as s:
            put_html('<h3>Popup Content</h3>')
            put_text('html: <br/>')
            put_buttons([('clear()', s)], onclick=clear)

        put_text('Also work!', scope=s)


    The context manager will open a new output scope and return the scope name.
    The output in the context manager will be displayed on the popup window by default.
    After the context manager exits, the popup window will not be closed.
    You can still use the ``scope`` parameter of the output function to output to the popup.

    * decorator:

    .. exportable-codeblock::
        :name: popup-decorator
        :summary: `popup()` as decorator

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
                                    dom_id=scope2dom(dom_id, no_css_selector=True)))

    return use_scope_(dom_id)


def close_popup():
    """Close the current popup window.

    See also: `popup()`
    """
    send_msg(cmd='close_popup')


def toast(content, duration=2, position='center', color='info', onclick=None):
    """Show a notification message.

    :param str content: Notification content.
    :param float duration: The duration of the notification display, in seconds. `0` means not to close automatically
        (at this time, a close button will be displayed next to the message, and the user can close the message manually)
    :param str position: Where to display the notification message. Available values are `'left'`, `'center'` and `'right'`.
    :param str color: Background color of the notification.
        Available values are `'info'`, `'error'`, `'warn'`, `'success'` or hexadecimal color value starting with `'#'`
    :param callable onclick: The callback function when the notification message is clicked.
        The callback function receives no parameters.

        Note: When in :ref:`Coroutine-based session <coroutine_based_session>`, the callback can be a coroutine function.

    Example:

    .. exportable-codeblock::
        :name: toast
        :summary: `toast()` usage

        def show_msg():
            put_text("You clicked the notification.")

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


def use_scope(name=None, clear=False, **kwargs):
    """use_scope(name=None, clear=False)

    Open or enter a scope. Can be used as context manager and decorator.

    See :ref:`User manual - use_scope() <use_scope>`

    :param str name: Scope name. If it is None, a globally unique scope name is generated.
        (When used as context manager, the context manager will return the scope name)
    :param bool clear: Whether to clear the contents of the scope before entering the scope.

    :Usage:

    ::

        with use_scope(...) as scope_name:
            put_xxx()

        @use_scope(...)
        def app():
            put_xxx()

    """
    # For backward compatible
    #     :param bool create_scope: Whether to create scope when scope does not exist.
    #     :param scope_params: Extra parameters passed to `set_scope()` when need to create scope.
    #         Only available when ``create_scope=True``.
    create_scope = kwargs.pop('create_scope', True)
    scope_params = kwargs

    if name is None:
        name = random_str(10)
    check_dom_name_value(name, 'scope name')

    def before_enter():
        if create_scope:
            if_exist = 'clear' if clear else None
            set_scope(name, if_exist=if_exist, **scope_params)

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
        """
        If this method returns True, it means that the context manager can handle the exception,
        so that the with statement terminates the propagation of the exception
        """
        get_current_session().pop_scope()
        return False  # Propagate Exception

    def __call__(self, func):
        """decorator implement"""

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
