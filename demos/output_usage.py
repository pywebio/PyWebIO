"""
Output demo
^^^^^^^^^^^^^^
Demonstrate various output usage supported by PyWebIO

:demo_host:`Demo </output_usage>`, `Source code <https://github.com/wang0618/PyWebIO/blob/dev/demos/output_usage.py>`_
"""
from pywebio import start_server
from pywebio.output import *
from pywebio.session import hold, info as session_info
from functools import partial


def t(eng, chinese):
    """return English or Chinese text according to the user's browser language"""
    return chinese if 'zh' in session_info.user_language else eng


def code_block(code, strip_indent=4):
    if strip_indent:
        lines = (
            i[strip_indent:] if (i[:strip_indent] == ' ' * strip_indent) else i
            for i in code.splitlines()
        )
        code = '\n'.join(lines)
    code = code.strip('\n')

    def run_code(code, scope):
        with use_scope(scope):
            exec(code, globals())

    with use_scope() as scope:
        put_code(code, 'python')
        put_buttons([{'label': t('Run', '运行'), 'value': '', 'color': 'success'}],
                    onclick=[partial(run_code, code=code, scope=scope)], small=True)


async def main():
    """PyWebIO Output Usage

    Demonstrate various output usage supported by PyWebIO.
    演示PyWebIO输出模块的使用
    """
    put_markdown(t("""# PyWebIO Output demo
    
    You can get the source code of this demo in [here](https://github.com/wang0618/PyWebIO/blob/dev/demos/output_usage.py)
    
    This demo only introduces part of the functions of the PyWebIO output module. For the complete features, please refer to the [User Guide](https://pywebio.readthedocs.io/zh_CN/latest/guide.html).
    
    The output functions are all defined in the `pywebio.output` module and can be imported using `from pywebio.output import *`.
    
    """, """# PyWebIO 输出演示
    
    在[这里](https://github.com/wang0618/PyWebIO/blob/dev/demos/output_usage.py)可以获取本Demo的源码。
    
    本Demo仅提供了PyWebIO输出模块的部分功能的演示，完整特性请参阅[用户指南](https://pywebio.readthedocs.io/zh_CN/latest/guide.html)。
    
    PyWebIO的输出函数都定义在 `pywebio.output` 模块中，可以使用 `from pywebio.output import *` 引入。

    ### 基本输出
    PyWebIO提供了一些便捷函数来输出表格、链接等格式:
    """), strip_indent=4)

    code_block(t(r"""
    # Text Output
    put_text("Hello world!")

    # Table Output
    put_table([
        ['Commodity', 'Price'],
        ['Apple', '5.5'],
        ['Banana', '7'],
    ])
    
    # Markdown Output
    put_markdown('~~Strikethrough~~')
    
    # File Output
    put_file('hello_word.txt', b'hello word!')
    """, r"""
    # 文本输出
    put_text("Hello world!")

    # 表格输出
    put_table([
        ['商品', '价格'],
        ['苹果', '5.5'],
        ['香蕉', '7'],
    ])

    # Markdown输出
    put_markdown('~~删除线~~')

    # 文件输出
    put_file('hello_word.txt', b'hello word!')
    """))

    put_markdown(t(r"""For all output functions provided by PyWebIO, please refer to the [document](https://pywebio.readthedocs.io/en/latest/output.html#output-func-list).
    
    ### Combined Output
    The output functions whose name starts with `put_` can be combined with some output functions as part of the final output:

    You can pass `put_xxx()` calls to `put_table()` as cell content:
    """, r"""PyWebIO提供的全部输出函数请参考[PyWebIO文档](https://pywebio.readthedocs.io/zh_CN/latest/output.html#output-func-list)
    
    ### 组合输出
    
    函数名以 `put_` 开始的输出函数，可以与一些输出函数组合使用，作为最终输出的一部分。

    比如`put_table()`支持以`put_xxx()`调用作为单元格内容:
    """), strip_indent=4)

    code_block(r"""
    put_table([
        ['Type', 'Content'],
        ['html', put_html('X<sup>2</sup>')],
        ['text', '<hr/>'],  # equal to ['text', put_text('<hr/>')]
        ['buttons', put_buttons(['A', 'B'], onclick=toast)],  
        ['markdown', put_markdown('`Awesome PyWebIO!`')],
        ['file', put_file('hello.text', b'hello world')],
        ['table', put_table([['A', 'B'], ['C', 'D']])]
    ])
    """)

    put_markdown(t(r"Similarly, you can pass `put_xxx()` calls to `popup()` as the popup content:",
                   r"类似地，`popup()`也可以将`put_xxx()`调用作为弹窗内容:"), strip_indent=4)

    code_block(r"""
    popup('Popup title', [
        put_html('<h3>Popup Content</h3>'),
        'plain html: <br/>',  # equal to put_text('plain html: <br/>')
        put_table([['A', 'B'], ['C', 'D']]),
        put_buttons(['close_popup()'], onclick=lambda _: close_popup())
    ])
    """)

    put_markdown(t(r"For more output functions that accept `put_xxx()` calls as parameters, please refer to the [document](https://pywebio.readthedocs.io/en/latest/output.html#output-func-list).",
                   r"更多接受`put_xxx()`作为参数的输出函数请参考[函数文档](https://pywebio.readthedocs.io/zh_CN/latest/output.html#output-func-list)。"))

    put_markdown(t(r"""### Callback
    PyWebIO allows you to output some buttons and bind callbacks to them. The provided callback function will be executed when the button is clicked.
    
    This is an example:%s
    The call to `put_table()` will not block. When user clicks a button, the corresponding callback function will be invoked:
    """, r"""### 事件回调
    PyWebIO允许你输出一些控件，当控件被点击时执行提供的回调函数，就像编写GUI程序一样。
    
    下面是一个例子:%s
    `put_table()`的调用不会阻塞。当用户点击了某行中的按钮时，PyWebIO会自动调用相应的回调函数:
    """) % """
    ```python
    from functools import partial

    def edit_row(choice, row):
        put_markdown("> You click`%s` button ar row `%s`" % (choice, row))

    put_table([
        ['Idx', 'Actions'],
        [1, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])
    ```
    """, strip_indent=4)

    from functools import partial

    @use_scope('table-callback')
    def edit_row(choice, row):
        put_markdown("> You click `%s` button ar row `%s`" % (choice, row))

    put_table([
        ['Idx', 'Actions'],
        [1, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])
    set_scope('table-callback')

    put_markdown(t("Of course, PyWebIO also supports outputting individual buttons:", "当然，PyWebIO还支持单独的按钮控件:")+r"""
    ```python
    def btn_click(btn_val):
        put_markdown("> You click `%s` button" % btn_val)

    put_buttons(['A', 'B', 'C'], onclick=btn_click)
    ```
    """, strip_indent=4)

    @use_scope('button-callback')
    def btn_click(btn_val):
        put_markdown("> You click `%s` button" % btn_val)

    put_buttons(['A', 'B', 'C'], onclick=btn_click)
    set_scope('button-callback')

    put_markdown(t(r"""### Output Scope
    
    PyWebIO uses the scope model to give more control to the location of content output. The output area of PyWebIO can be divided into different output domains. The output domain is called Scope in PyWebIO.

    The output domain is a container of output content, and each output domain is arranged vertically, and the output domains can also be nested.

    Each output function (function name like `put_xxx()`) will output its content to a scope, the default is "current scope". "current scope" is determined by the runtime context. The output function can also manually specify the scope to output. The scope name is unique within the session.
    
    You can use `use_scope()` to open and enter a new output scope, or enter an existing output scope: %s
    The above code will generate the following Scope layout:
    """, r"""### 输出域Scope

    PyWebIO使用Scope模型来对内容输出的位置进行灵活地控制，PyWebIO的内容输出区可以划分出不同的输出域，PyWebIO将输出域称作`Scope`。
    
    输出域为输出内容的容器，各个输出域之间上下排列，输出域也可以进行嵌套。
    
    每个输出函数（函数名形如 `put_xxx()` ）都会将内容输出到一个Scope，默认为”当前Scope”，”当前Scope”由运行时上下文确定，输出函数也可以手动指定输出到的Scope。Scope名在会话内唯一。
    
    可以使用 `use_scope()` 开启并进入一个新的输出域，或进入一个已经存在的输出域: %s
    以上代码将会产生如下Scope布局:
    """) % """
    ```python
    with use_scope('A'):
        put_text('Text in scope A')
    
        with use_scope('B'):
            put_text('Text in scope B')
    
    with use_scope('C'):
        put_text('Text in scope C')
    ```
    """, strip_indent=4)
    with use_scope('A'):
        put_text('Text in scope A')

        with use_scope('B'):
            put_text('Text in scope B')

    with use_scope('C'):
        put_text('Text in scope C')

    put_html("""<style>                                           
    #pywebio-scope-A {border: 1px solid red;}                    
    #pywebio-scope-B {border: 1px solid blue;margin:2px}         
    #pywebio-scope-C {border: 1px solid green;margin-top:2px}    
    </style><br/>""")

    put_markdown(t(r"""The output function (function name like `put_xxx()`) will output the content to the "current scope" by default, and the "current scope" of the runtime context can be set by `use_scope()`.
    
    In addition, you can use the `scope` parameter of the output function to specify the destination scope to output:
    """, r"""
    输出函数（函数名形如 `put_xxx()` ）在默认情况下，会将内容输出到”当前Scope”，可以通过 `use_scope()` 设置运行时上下文的”当前Scope”。
    
    此外，也可以通过输出函数的 scope 参数指定输出的目的Scope:
    """), strip_indent=4)

    put_grid([
        [put_code("put_text('A', scope='A')", 'python'), None, put_buttons([t('Run', '运行')], [lambda: put_text('A', scope='A')])],
        [put_code("put_text('B', scope='B')", 'python'), None, put_buttons([t('Run', '运行')], [lambda: put_text('B', scope='B')])],
        [put_code("put_text('C', scope='C')", 'python'), None, put_buttons([t('Run', '运行')], [lambda: put_text('C', scope='C')])],
    ], cell_widths='1fr 10px auto')

    put_markdown(t("The output content can be inserted into any positions of the target scope by using the `position` parameter of the output function.", "输出函数可以使用`position`参数指定内容在Scope中输出的位置") + """
    ```python
    put_text(now(), scope='A', position=...)
    ```
    """, strip_indent=4)
    import datetime

    put_buttons([('position=%s' % i, i) for i in [1, 2, 3, -1, -2, -3]],
                lambda i: put_text(datetime.datetime.now(), position=i, scope='A'), small=True)

    put_markdown(t(r"In addition to `use_scope()`, PyWebIO also provides the following scope control functions:",
                   r"除了 `use_scope()` , PyWebIO同样提供了以下scope控制函数： "))

    put_grid([
        [put_code("clear('B')  # Clear content of Scope B", 'python'), None, put_buttons(['运行'], [lambda: clear('B')])],
        [put_code("remove('C')  # Remove Scope C", 'python'), None, put_buttons(['运行'], [lambda: remove('C')])],
        [put_code("scroll_to('A')  # Scroll the page to position of Scope A", 'python'), None, put_buttons(['运行'], [lambda: scroll_to('A')])],
    ], cell_widths='1fr 10px auto')

    put_markdown(t(r"""### Layout
    
    In general, using the various output functions introduced above is enough to output what you want, but these outputs are arranged vertically. If you want to make a more complex layout (such as displaying a code block on the left side of the page and an image on the right), you need to use layout functions.
    
    The `pywebio.output` module provides 3 layout functions, and you can create complex layouts by combining them:
    
     - `put_row()` : Use row layout to output content. The content is arranged horizontally
     - `put_column()` : Use column layout to output content. The content is arranged vertically
     - `put_grid()` : Output content using grid layout
    
    Here is an example by combining `put_row()` and `put_column()`:
    """, r"""### 布局
    一般情况下，使用上文介绍的各种输出函数足以完成各种内容的展示，但直接调用输出函数产生的输出之间都是竖直排列的，如果想实现更复杂的布局（比如在页 面左侧显示一个代码块，在右侧显示一个图像），就需要借助布局函数。

    `pywebio.output` 模块提供了3个布局函数，通过对他们进行组合可以完成各种复杂的布局:
    
     - `put_row()` : 使用行布局输出内容. 内容在水平方向上排列
     - `put_column()` : 使用列布局输出内容. 内容在竖直方向上排列
     - `put_grid()` : 使用网格布局输出内容

    比如，通过通过组合 `put_row()` 和 `put_column()` 实现的布局:
    """), strip_indent=4)

    code_block(r"""
    put_row([
        put_column([
            put_code('A'),
            put_row([
                put_code('B1'), None,  # %s
                put_code('B2'), None,
                put_code('B3'),
            ]),
            put_code('C'),
        ]), None,
        put_code('D'), None,
        put_code('E')
    ])
    """ % t('None represents the space between the output', 'None 表示输出之间的空白'))

    put_markdown(t(r"""### Style
    If you are familiar with CSS styles, you can use the `style()` function to set a custom style for the output.

    You can set the CSS style for a single `put_xxx()` output:
    """, r"""### 样式
    
    如果你熟悉 CSS样式 ，你还可以使用 `style()` 函数给输出设定自定义样式。

    可以给单个的 `put_xxx()` 输出设定CSS样式，也可以配合组合输出使用:
    """), strip_indent=4)

    code_block(r"""
    style(put_text('Red'), 'color: red')
    
    put_table([
        ['A', 'B'],
        ['C', style(put_text('Red'), 'color: red')],
    ])
    """, strip_indent=4)

    put_markdown(t(r"`style()` also accepts a list of output calls:", r"`style()` 也接受列表作为输入:"))

    code_block(r"""
    style([
        put_text('Red'),
        put_markdown('~~del~~')
    ], 'color: red')
    
    put_collapse('title', style([
        put_text('text'),
        put_markdown('~~del~~'),
    ], 'margin-left: 20px'))

    """, strip_indent=4)

    put_markdown(t("""----
    For more information about output of PyWebIO, please visit PyWebIO [User Guide](https://pywebio.readthedocs.io/zh_CN/latest/guide.html) and [output module documentation](https://pywebio.readthedocs.io/zh_CN/latest/output.html).
    ""","""----
    PyWebIO的输出演示到这里就结束了，更多内容请访问PyWebIO[用户指南](https://pywebio.readthedocs.io/zh_CN/latest/guide.html)和[output模块文档](https://pywebio.readthedocs.io/zh_CN/latest/output.html)。
    """), lstrip=True)

    await hold()


if __name__ == '__main__':
    start_server(main, debug=True, port=8080, cdn=False)
