User's guide
============

如果你接触过Web开发，你可能对接下来描述的PyWebIO的用法感到不太习惯，不同于传统Web开发的后端实现接口、前端进行展示交互的模式，在PyWebIO中，所有的逻辑都通过编写Python代码实现。

你可以按照编写控制台程序的逻辑编写PyWebIO应用，只不过这里的终端变成了浏览器。通过PyWebIO提供的命令式API，
你可以简单地调用 ``put_text`` 、 ``put_image`` 、 ``put_table`` 等函数输出文本、图片、表格等内容到浏览器，也可以调用 ``input`` 、 ``select`` 、
``file_upload`` 等函数在浏览器上显示不同表单来接收用户的输入。此外PyWebIO中还提供了点击事件、布局等支持，让你可以使用最少的代码完成与用户的交互，
并尽可能提供良好的用户体验。

本篇使用指南从几个方面对PyWebIO的使用进行介绍，覆盖了PyWebIO的绝大部分特性。本文档中大部分示例代码的右上方都有一个Demo链接，点击后可以在线预览代码的运行效果。

输入
------------

输入函数都定义在 :doc:`pywebio.input </input>` 模块中，可以使用 ``from pywebio.input import *`` 引入。

调用输入函数会在浏览器上弹出一个输入表单来获取输入。PyWebIO的输入函数是阻塞式的（和Python内置的 `input` 一样），在表单被成功提交之前，输入函数不会返回。

基本输入
^^^^^^^^^^^

首先是一些基本类型的输入

文本输入:

.. exportable-codeblock::
    :name: text-input
    :summary: 文本输入

    age = input("How old are you?", type=NUMBER)
    put_text('age = %r' % age)  # ..demo-only

这样一行代码的效果为：浏览器会弹出一个文本输入框来获取输入，在用户完成输入将表单提交后，函数返回用户输入的值。

下面是一些其他类型的输入函数:

.. exportable-codeblock::
    :name: basic-input
    :summary: 基本输入

    # 密码输入
    password = input("Input password", type=PASSWORD)
    put_text('password = %r' % password)  # ..demo-only
    ## ----

    # 下拉选择框
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    put_text('gift = %r' % gift)  # ..demo-only
    ## ----

    # 勾选选项
    agree = checkbox("用户协议", options=['I agree to terms and conditions'])
    put_text('agree = %r' % agree)  # ..demo-only
    ## ----

    # 单选选项
    answer = radio("Choose one", options=['A', 'B', 'C', 'D'])
    put_text('answer = %r' % answer)  # ..demo-only
    ## ----

    # 多行文本输入
    text = textarea('Text Area', rows=3, placeholder='Some text')
    put_text('text = %r' % text)  # ..demo-only
    ## ----

    # 文件上传
    img = file_upload("Select a image:", accept="image/*")
    if img:    # ..demo-only
        put_image(img['content'], title=img['filename'])  # ..demo-only


输入选项
^^^^^^^^^^^

输入函数可指定的参数非常丰富（全部参数及含义请见 :doc:`函数文档 </input>` ）:

.. exportable-codeblock::
    :name: input-args
    :summary: 输入参数

    input('This is label', type=TEXT, placeholder='This is placeholder',
            help_text='This is help text', required=True)

以上代码将在浏览器上显示如下：

.. image:: /assets/input_1.png

我们可以为输入指定校验函数，校验函数应在校验通过时返回None，否则返回错误消息:

.. exportable-codeblock::
    :name: input-valid-func
    :summary: 输入指定校验函数

    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = input("How old are you?", type=NUMBER, validate=check_age)
    put_text('age = %r' % age)  # ..demo-only

当用户输入了不合法的值时，页面上的显示如下:

.. image:: /assets/input_2.png


:func:`pywebio.input.textarea` 还支持使用 `Codemirror <https://codemirror.net/>`_ 实现代码风格的编辑区，只需使用 ``code`` 参数传入Codemirror支持的选项即可(最简单的情况是直接传入 ``code={}`` 或 ``code=True``):

.. exportable-codeblock::
    :name: codemirror
    :summary: textarea代码编辑

    code = textarea('Code Edit', code={
        'mode': "python",  # 编辑区代码语言
        'theme': 'darcula',  # 编辑区darcula主题, Visit https://codemirror.net/demo/theme.html#cobalt to get more themes
    }, value='import something\n# Write your python code')
    put_code(code, language='python')  # ..demo-only

文本框的显示效果为：

.. image:: /assets/codemirror_textarea.png

:ref:`这里 <codemirror_options>` 列举了一些常用的Codemirror选项，完整的Codemirror选项请见：https://codemirror.net/doc/manual.html#config

输入组
^^^^^^^

PyWebIO支持输入组, 返回结果为一个字典。`pywebio.input.input_group()` 接受单项输入组成的列表作为参数, 返回以单项输入函数中的 ``name`` 作为键、以输入数据为值的字典:

.. exportable-codeblock::
    :name: input-group
    :summary: 输入组

    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息  # ..demo-only
        if p < 10:                  # ..demo-only
            return 'Too young!!'    # ..demo-only
        if p > 60:                  # ..demo-only
            return 'Too old!!'      # ..demo-only
                                    # ..demo-only
    data = input_group("Basic info",[
      input('Input your name', name='name'),
      input('Input your age', name='age', type=NUMBER, validate=check_age)
    ])
    put_text(data['name'], data['age'])

输入组中同样支持使用 ``validate`` 参数设置校验函数，其接受整个表单数据作为参数:

.. exportable-codeblock::
    :name: input-group
    :summary: 输入组

    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息  # ..demo-only
        if p < 10:                  # ..demo-only
            return 'Too young!!'    # ..demo-only
        if p > 60:                  # ..demo-only
            return 'Too old!!'      # ..demo-only
                                    # ..demo-only
    def check_form(data):  # 检验函数校验通过时返回None，否则返回 (input name,错误消息)
        if len(data['name']) > 6:
            return ('name', '名字太长！')
        if data['age'] <= 0:
            return ('age', '年龄不能为负数！')

    data = input_group("Basic info",[           # ..demo-only
       input('Input your name', name='name'),   # ..demo-only
       input('Input your age', name='age', type=NUMBER, validate=check_age)  # ..demo-only
    ], validate=check_form)              # ..demo-only
    put_text(data['name'], data['age'])    # ..demo-only

.. attention::
   PyWebIO 根据是否在输入函数中传入 ``name`` 参数来判断输入函数是在 `input_group` 中还是被单独调用。
   所以当单独调用一个输入函数时, **不要** 设置 ``name`` 参数；而在 `input_group` 中调用输入函数时，需 **务必提供** ``name`` 参数

输出
------------

输出函数都定义在 :doc:`pywebio.output </output>` 模块中，可以使用 ``from pywebio.output import *`` 引入。

调用输出函数后，内容会实时输出到浏览器，在应用的生命周期内，可以在任意时刻调用输出函数。

基本输出
^^^^^^^^^^^^^^

PyWebIO提供了一系列函数来输出表格、链接等格式:

.. exportable-codeblock::
    :name: basic-output
    :summary: 基本输出

    # 文本输出
    put_text("Hello world!")
    ## ----

    # 表格输出
    put_table([
        ['商品', '价格'],
        ['苹果', '5.5'],
        ['香蕉', '7'],
    ])
    ## ----

    # Markdown输出
    put_markdown('~~删除线~~')
    ## ----

    # 文件输出
    put_file('hello_word.txt', b'hello word!')
    ## ----

    # 显示一个弹窗
    popup('popup title', 'popup text content')


PyWebIO提供的全部输出函数见 :doc:`pywebio.output </output>` 模块。另外，PyWebIO还支持一些第三方库来进行数据可视化，参见 :doc:`第三方库生态 </libraries_support>` 。

.. _combine_output:

组合输出
^^^^^^^^^^^^^^
函数名以 ``put_`` 开始的输出函数，可以与一些输出函数组合使用，作为最终输出的一部分：

`put_table() <pywebio.output.put_table>` 支持以 ``put_xxx()`` 调用作为单元格内容:

.. exportable-codeblock::
    :name: putxxx
    :summary: 组合输出

    put_table([
        ['Type', 'Content'],
        ['html', put_html('X<sup>2</sup>')],
        ['text', '<hr/>'],  # 等价于 ['text', put_text('<hr/>')]
        ['buttons', put_buttons(['A', 'B'], onclick=...)],  # ..doc-only
        ['buttons', put_buttons(['A', 'B'], onclick=put_text)],  # ..demo-only
        ['markdown', put_markdown('`Awesome PyWebIO!`')],
        ['file', put_file('hello.text', b'hello world')],
        ['table', put_table([['A', 'B'], ['C', 'D']])]
    ])

上例显示效果如下:

.. image:: /assets/put_table.png

类似地， `popup() <pywebio.output.popup>` 也可以将 ``put_xxx()`` 调用作为弹窗内容:

.. exportable-codeblock::
    :name: popup
    :summary: 弹窗

    popup('Popup title', [
        put_html('<h3>Popup Content</h3>'),
        'plain html: <br/>',  # 等价于 put_text('plain html: <br/>')
        put_table([['A', 'B'], ['C', 'D']]),
        put_buttons(['close_popup()'], onclick=lambda _: close_popup())
    ])

其他接受 ``put_xxx()`` 调用作为参数的输出函数还有 `put_collapse() <pywebio.output.put_collapse>` 、 `put_scrollable() <pywebio.output.put_scrollable>` 、`put_row() <pywebio.output.put_row>` 等,
此外，还可以通过 `put_widget() <pywebio.output.put_widget>` 自定义可接收 ``put_xxx()`` 调用的输出组件，具体用法请参考函数文档。

使用组合输出时，如果想在内容输出后，对其中的 ``put_xxx()`` 子项进行动态修改，可以使用 `output() <pywebio.output.output>` 函数，
`output() <pywebio.output.output>` 就像一个占位符，它可以像 ``put_xxx()`` 一样传入 `put_table` 、 `popup` 、 `put_widget` 等函数中作为输出的一部分，
并且，在输出后，还可以对其中的内容进行修改(比如重置或增加内容):

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


事件回调
^^^^^^^^^^^^^^

从上面可以看出，PyWebIO把交互分成了输入和输出两部分：输入函数为阻塞式调用，会在用户浏览器上显示一个表单，在用户提交表单之前输入函数将不会返回；输出函数将内容实时输出至浏览器。这种交互方式和控制台程序是一致的，因此PyWebIO应用非常适合使用控制台程序的编写逻辑来进行开发。

此外，PyWebIO还支持事件回调：PyWebIO允许你输出一些控件，当控件被点击时执行提供的回调函数。

下面是一个例子:

.. exportable-codeblock::
    :name: onclick-callback
    :summary: 事件回调

    from functools import partial

    def edit_row(choice, row):
        put_text("You click %s button ar row %s" % (choice, row))

    put_table([
        ['Idx', 'Actions'],
        [1, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, put_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])

`put_table() <pywebio.output.put_table>` 的调用不会阻塞。当用户点击了某行中的按钮时，PyWebIO会自动调用相应的回调函数:

.. image:: /assets/table_onclick.*

当然，PyWebIO还支持单独的按钮控件:

.. exportable-codeblock::
    :name: put-buttons
    :summary: 按钮控件

    def btn_click(btn_val):
        put_text("You click %s button" % btn_val)
    put_buttons(['A', 'B', 'C'], onclick=btn_click)

.. note::
   在PyWebIO会话(关于会话的概念见下文 :ref:`Server与script模式 <server_and_script_mode>` )结束后，事件回调也将不起作用，你可以在任务函数末尾处使用 :func:`pywebio.session.hold()` 函数来将会话保持，这样在用户关闭浏览器页面前，事件回调将一直可用。

输出域Scope
^^^^^^^^^^^^^^
PyWebIO使用Scope模型来对内容输出的位置进行灵活地控制，PyWebIO的内容输出区可以划分出不同的输出域，PyWebIO将输出域称作 `Scope` 。

输出域为输出内容的容器，各个输出域之间上下排列，输出域也可以进行嵌套。

每个输出函数（函数名形如 `put_xxx()` ）都会将内容输出到一个Scope，默认为"当前Scope"，"当前Scope"由运行时上下文确定，输出函数也可以手动指定输出到的Scope。Scope名在会话内唯一。

.. _use_scope:

**use_scope()**

可以使用 `use_scope() <pywebio.output.use_scope>` 开启并进入一个新的输出域，或进入一个已经存在的输出域:

.. exportable-codeblock::
    :name: use-scope
    :summary: 使用`use_scope()`创建或进入输出域

    with use_scope('scope1'):  # 创建并进入scope 'scope1'
        put_text('text1 in scope1')

    put_text('text in parent scope of scope1')

    with use_scope('scope1'):  # 进入之前创建的scope 'scope1'
        put_text('text2 in scope1')

以上代码将会输出::

    text1 in scope1
    text2 in scope1
    text in parent scope of scope1

`use_scope() <pywebio.output.use_scope>` 还可以使用 `clear` 参数将scope中原有的内容清空:

.. exportable-codeblock::
    :name: use-scope
    :summary: 使用`use_scope()`清空输出域内容

    with use_scope('scope2'):
        put_text('create scope2')

    put_text('text in parent scope of scope2')
    ## ----

    with use_scope('scope2', clear=True):  # 进入之前创建的scope2，并清空原有内容
        put_text('text in scope2')

以上代码将会输出::

    text in scope2
    text in parent scope of scope2

`use_scope() <pywebio.output.use_scope>` 还可以作为装饰器来使用:

.. exportable-codeblock::
    :name: use-scope-decorator
    :summary: `use_scope()`作为装饰器来使用

    import time  # ..demo-only
    from datetime import datetime

    @use_scope('time', clear=True)
    def show_time():
        put_text(datetime.now())

    while 1:          # ..demo-only
       show_time()    # ..demo-only
       time.sleep(1)  # ..demo-only

第一次调用 ``show_time`` 时，将会在当前位置创建 ``time`` 输出域并在其中输出当前时间，之后每次调用 ``show_time()`` ，时间都会输出到相同的区域。

Scope是可嵌套的，初始条件下，PyWebIO应用只有一个最顶层的 ``ROOT`` Scope。每创建一个新Scope，Scope的嵌套层级便会多加一层，每退出当前Scope，Scope的嵌套层级便会减少一层。
PyWebIO使用Scope栈来保存运行时的Scope的嵌套层级。

例如，如下代码将会创建3个Scope:

.. exportable-codeblock::
    :name: use-scope-nested
    :summary: 嵌套Scope

    with use_scope('A'):
        put_text('Text in scope A')

        with use_scope('B'):
            put_text('Text in scope B')

    with use_scope('C'):
        put_text('Text in scope C')

    put_html("""<style>                                          # ..demo-only
    #pywebio-scope-A {border: 1px solid red;}                    # ..demo-only
    #pywebio-scope-B {border: 1px solid blue;margin:2px}         # ..demo-only
    #pywebio-scope-C {border: 1px solid green;margin-top:2px}    # ..demo-only
    </style>""")                                                 # ..demo-only
    put_text()                                                   # ..demo-only
    put_buttons([('Put text to %s' % i, i) for i in ('A', 'B', 'C')], lambda s: put_text(s, scope=s))  # ..demo-only


以上代码将会产生如下Scope布局::

   ┌─ROOT────────────────────┐
   │                         │
   │ ┌─A───────────────────┐ │
   │ │ Text in scope A     │ │
   │ │ ┌─B───────────────┐ │ │
   │ │ │ Text in scope B │ │ │
   │ │ └─────────────────┘ │ │
   │ └─────────────────────┘ │
   │                         │
   │ ┌─C───────────────────┐ │
   │ │ Text in scope C     │ │
   │ └─────────────────────┘ │
   └─────────────────────────┘

.. _scope_param:

**输出函数的scope相关参数**

输出函数（函数名形如 ``put_xxx()`` ）在默认情况下，会将内容输出到"当前Scope"，可以通过 ``use_scope()`` 设置运行时上下文的"当前Scope"。

此外，也可以通过输出函数的 ``scope`` 参数指定输出的目的Scope:

.. exportable-codeblock::
    :name: put-xxx-scope
    :summary: 输出函数的`scope`参数

    with use_scope('scope3'):
        put_text('text1 in scope3')   # 输出到当前Scope：scope3
        put_text('text in ROOT scope', scope='ROOT')   # 输出到ROOT Scope

    put_text('text2 in scope3', scope='scope3')   # 输出到scope3

以上将会输出::

    text1 in scope3
    text2 in scope3
    text in ROOT scope

``scope`` 参数除了直接指定目标Scope名，还可以使用一个整形通过索引Scope栈来确定Scope：0表示最顶层也就是ROOT Scope，-1表示当前Scope，-2表示进入当前Scope前所使用的Scope，......

默认条件下，在同一Scope中的输出内容，会根据输出函数的调用顺序从上往下排列，最后调用的输出函数会输出内容到目标Scope的底部。通过输出函数的 ``position`` 参数可以将输出内容插入到目标Scope的其他位置。

一个Scope中各次输出的元素具有像数组一样的索引，最前面的编号为0，以此往后递增加一；同样可以使用负数对Scope中的元素进行索引，-1表示最后面的元素，-2表示次后面的元素......

``position`` 参数类型为整形， ``position>=0`` 时表示输出内容到目标Scope的第position号元素的前面； ``position<0`` 时表示输出内容到目标Scope第position号元素之后:

.. exportable-codeblock::
    :name: put-xxx-position
    :summary: 输出函数的`position`参数

    with use_scope('scope1'):
        put_text('A')               # 输出内容: A
    ## ----
    with use_scope('scope1'):  # ..demo-only
        put_text('B', position=0)   # 输出内容: B A
    ## ----
    with use_scope('scope1'):  # ..demo-only
        put_text('C', position=-2)  # 输出内容: B C A
    ## ----
    with use_scope('scope1'):  # ..demo-only
        put_text('D', position=1)   # 输出内容: B D C A

**输出域控制函数**

除了 `use_scope()` , PyWebIO同样提供了以下scope控制函数：

* `set_scope(name) <pywebio.output.set_scope>` : 在当前位置（或指定位置）创建scope
* `clear(scope) <pywebio.output.clear>` : 清除scope的内容
* `remove(scope) <pywebio.output.remove>` : 移除scope
* `scroll_to(scope) <pywebio.output.scroll_to>` : 将页面滚动到scope处


页面环境设置
^^^^^^^^^^^^^^

**页面标题**

调用 `set_env(title=...) <pywebio.session.set_env>` 可以设置页面标题。

**自动滚动**

在进行一些持续性的输出时(比如日志输出)，有时希望在有新输出后自动将页面滚动到最下方，这时可以调用 `set_env(auto_scroll_bottom=True) <pywebio.session.set_env>` 来开启自动滚动。
注意，开启后，只有输出到ROOT Scope才可以触发自动滚动。

**输出动画**

PyWebIO在输出内容时默认会使用淡入的动画效果来显示内容，可使用 `set_env(output_animation=False) <pywebio.session.set_env>` 来关闭动画。

有关不同环境配置的效果可查看 :demo_host:`set_env Demo </?pywebio_api=set_env_demo>`

布局
^^^^^^^^^^^^^^
一般情况下，使用上文介绍的各种输出函数足以完成各种内容的展示，但直接调用输出函数产生的输出之间都是竖直排列的，如果想实现更复杂的布局（比如在页面左侧显示一个代码块，在右侧显示一个图像），就需要借助布局函数。

``pywebio.output`` 模块提供了3个布局函数，通过对他们进行组合可以完成各种复杂的布局:

* `put_row() <pywebio.output.put_row>` : 使用行布局输出内容. 内容在水平方向上排列
* `put_column() <pywebio.output.put_column>` : 使用列布局输出内容. 内容在竖直方向上排列
* `put_grid() <pywebio.output.put_grid>` : 使用网格布局输出内容

通过组合 ``put_row()`` 和 ``put_column()`` 可以实现灵活布局:

.. exportable-codeblock::
    :name: put-row-column
    :summary: 布局函数

    put_row([
        put_column([
            put_code('A'),
            put_row([
                put_code('B1'), None,  # None 表示输出之间的空白
                put_code('B2'), None,
                put_code('B3'),
            ]),
            put_code('C'),
        ]), None,
        put_code('D'), None,
        put_code('E')
    ])

显示效果如下:

.. image:: /assets/layout.png
   :align: center

布局函数还支持自定义各部分的尺寸::

    put_row([put_image(...), put_image(...)], size='40% 60%')  # 左右两图宽度比2:3

更多布局函数的用法及代码示例请查阅 :ref:`布局函数文档 <style_and_layout>` .

样式
^^^^^^^^^^^^^^
如果你熟悉 `CSS样式 <https://www.google.com/search?q=CSS%E6%A0%B7%E5%BC%8F>`_ ，你还可以使用 `style() <pywebio.output.style>` 函数给输出设定自定义样式。

可以给单个的 ``put_xxx()`` 输出设定CSS样式，也可以配合组合输出使用:

.. exportable-codeblock::
    :name: style
    :summary: 输出样式

    style(put_text('Red'), 'color: red')

    ## ----
    put_table([
        ['A', 'B'],
        ['C', style(put_text('Red'), 'color: red')],
    ])

``style()`` 也接受列表作为输入，``style()`` 会为列表的每一项都设置CSS样式，返回值可以直接输出，可用于任何接受 ``put_xxx()`` 列表的地方:

.. exportable-codeblock::
    :name: style-list
    :summary: 批量设置输出样式

    style([
        put_text('Red'),
        put_markdown('~~del~~')
    ], 'color: red')

    ## ----
    put_collapse('title', style([
        put_text('text'),
        put_markdown('~~del~~'),
    ], 'margin-left: 20px'))


.. _server_and_script_mode:

Server模式与Script模式
------------------------------------

在 :ref:`Hello, world <hello_word>` 一节中，已经知道，PyWebIO支持在普通的脚本中调用和使用
`start_server() <pywebio.platform.tornado.start_server>` 启动一个Web服务两种模式。

**Server模式**

在Server模式下，PyWebIO会启动一个Web服务来持续性地提供服务。需要提供一个任务函数(类似于Web开发中的视图函数)，当用户访问服务地址时，PyWebIO会开启一个新会话并运行任务函数。

使用 `start_server() <pywebio.platform.tornado.start_server>` 来启动PyWebIO的Server模式， `start_server() <pywebio.platform.tornado.start_server>` 除了接收一个函数作为任务函数外，
还支持传入函数列表或字典，从而使一个PyWebIO Server下可以有多个不同功能的服务，服务之间可以通过 `go_app() <pywebio.session.go_app>` 进行跳转，详细内容见函数文档。

.. attention::

    注意，在Server模式下，仅能在任务函数上下文中对PyWebIO的交互函数进行调用。比如如下调用是 **不被允许的** ::

        import pywebio
        from pywebio.input import input

        port = input('Input port number:')   # ❌ 在任务函数上下文之外调用了PyWebIO交互函数！！
        pywebio.start_server(my_task_func, port=int(port))


**Script模式**

Script模式下，在任何位置都可以调用PyWebIO的交互函数。

如果用户在会话结束之前关闭了浏览器，那么之后会话内对于PyWebIO交互函数的调用将会引发一个 `SessionException <pywebio.exceptions.SessionException>` 异常。

.. _thread_in_server_mode:

并发
^^^^^^^^^^^^^^

PyWebIO 支持在多线程环境中使用。

**Script模式**

在 Script模式下，你可以自由地启动线程，并在其中调用PyWebIO的交互函数。当所有非 `Daemon线程 <https://docs.python.org/3/library/threading.html#thread-objects>`_ 运行结束后，脚本退出。

**Server模式**

Server模式下，如果需要在新创建的线程中使用PyWebIO的交互函数，需要手动调用 `register_thread(thread) <pywebio.session.register_thread>` 对新进程进行注册（这样PyWebIO才能知道新创建的线程属于哪个会话）。
如果新创建的线程中没有使用到PyWebIO的交互函数，则无需注册。没有使用 `register_thread(thread) <pywebio.session.register_thread>` 注册的线程不受会话管理，其调用PyWebIO的交互函数将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` 异常。
当会话的任务函数和会话内通过 `register_thread(thread) <pywebio.session.register_thread>` 注册的线程都结束运行时，会话关闭。

Server模式下多线程的使用示例::

   def show_time():
       while True:
           with use_scope(name='time', clear=True):
               put_text(datetime.datetime.now())
               time.sleep(1)

   def app():
       t = threading.Thread(target=show_time)
       register_thread(t)
       put_markdown('## Clock')
       t.start()  # 在后台运行show_time()

       # ❌ 没有使用register_thread注册的线程调用PyWebIO交互函数会产生异常
       threading.Thread(target=show_time).start()

       put_text('Background task started.')


   start_server(app, port=8080, debug=True)


.. _session_close:

会话的结束
^^^^^^^^^^^^^^

会话还会因为用户的关闭浏览器而结束，这时当前会话内还未返回的PyWebIO输入函数调用将抛出 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常，之后对于PyWebIO交互函数的调用将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` 或 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常。

可以使用 `defer_call(func) <pywebio.session.defer_call>` 来设置会话结束时需要调用的函数。无论是因为用户主动关闭页面还是任务结束使得会话关闭，设置的函数都会被执行。
`defer_call(func) <pywebio.session.defer_call>` 可以用于资源清理等工作。在会话中可以多次调用 `defer_call() <pywebio.session.defer_call>` ,会话结束后将会顺序执行设置的函数。


与Web框架集成
---------------

.. _integration_web_framework:

可以将PyWebIO应用集成到现有的Python Web项目中，PyWebIO应用与Web项目共用一个Web框架。目前支持与Flask、Tornado、Django和aiohttp Web框架的集成。

与Web框架集成需要完成两部分配置：托管PyWebIO前端静态文件；暴露PyWebIO后端接口。这其中需要注意前端页面和后端接口的路径约定，
以及前端静态文件与后端接口分开部署时因为跨域而需要的特别设置。

集成方法
^^^^^^^^^^^

不同Web框架的集成方法如下：

.. tabs::

   .. tab:: Tornado

        需要在Tornado应用中引入两个 ``RequestHandler`` ,
        一个 ``RequestHandler`` 用来提供静态的前端文件，另一个 ``RequestHandler`` 用来和浏览器进行WebSocket通讯::

            import tornado.ioloop
            import tornado.web
            from pywebio.platform.tornado import webio_handler
            from pywebio import STATIC_PATH

            class MainHandler(tornado.web.RequestHandler):
                def get(self):
                    self.write("Hello, world")

            if __name__ == "__main__":
                application = tornado.web.Application([
                    (r"/", MainHandler),
                    (r"/tool/io", webio_handler(task_func)),  # task_func 为使用PyWebIO编写的任务函数
                    (r"/tool/(.*)", tornado.web.StaticFileHandler,
                          {"path": STATIC_PATH, 'default_filename': 'index.html'})  # 前端静态文件托管
                ])
                application.listen(port=80, address='localhost')
                tornado.ioloop.IOLoop.current().start()

        以上代码调用 `webio_handler(task_func) <pywebio.platform.tornado.webio_handler>` 来获得PyWebIO和浏览器进行通讯的Tornado `WebSocketHandler <https://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketHandler>`_ ，
        并将其绑定在 ``/tool/io`` 路径下；同时将PyWebIO的静态文件使用 `tornado.web.StaticFileHandler <https://www.tornadoweb.org/en/stable/web.html?highlight=StaticFileHandler#tornado.web.StaticFileHandler>`_ 托管到 ``/tool/(.*)`` 路径下。
        启动Tornado服务器后，访问 ``http://localhost/tool/`` 即可打开PyWebIO应用

        .. attention::

           当使用Tornado后端时，PyWebIO使用WebSocket协议和浏览器进行通讯，如果你的Tornado应用处在反向代理(比如Nginx)之后，
           可能需要特别配置反向代理来支持WebSocket协议，:ref:`这里 <nginx_ws_config>` 有一个Nginx配置WebSocket的例子。

   .. tab:: Flask

        需要添加两个PyWebIO相关的路由：一个用来提供静态的前端文件，另一个用来和浏览器进行Http通讯::

            from pywebio.platform.flask import webio_view
            from pywebio import STATIC_PATH
            from flask import Flask, send_from_directory

            app = Flask(__name__)

            # task_func 为使用PyWebIO编写的任务函数
            app.add_url_rule('/io', 'webio_view', webio_view(task_func),
                        methods=['GET', 'POST', 'OPTIONS'])  # 接口需要能接收GET、POST和OPTIONS请求

            @app.route('/')
            @app.route('/<path:static_file>')
            def serve_static_file(static_file='index.html'):
                """前端静态文件托管"""
                return send_from_directory(STATIC_PATH, static_file)

            app.run(host='localhost', port=80)

        以上代码使用 `webio_view(task_func) <pywebio.platform.flask.webio_view>` 来获得运行PyWebIO应用的Flask视图 ，
        并调用 `Flask.add_url_rule <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.add_url_rule>`_ 将其绑定在 ``/io`` 路径下；同时编写视图函数 ``serve_static_file`` 将PyWebIO使用的静态文件托管到 ``/`` 路径下。
        启动Flask应用后，访问 ``http://localhost/`` 即可打开PyWebIO应用

   .. tab:: Django

        在django的路由配置文件 ``urls.py`` 中加入PyWebIO相关的路由即可::

            # urls.py

            from functools import partial
            from django.urls import path
            from django.views.static import serve
            from pywebio import STATIC_PATH
            from pywebio.platform.django import webio_view

            # task_func 为使用PyWebIO编写的任务函数
            webio_view_func = webio_view(task_func)

            urlpatterns = [
                path(r"io", webio_view_func),  # http通信接口
                path(r'', partial(serve, path='index.html'), {'document_root': STATIC_PATH}),  # 前端index.html文件托管
                path(r'<path:path>', serve, {'document_root': STATIC_PATH}),  # 前端其他文件托管
            ]

        需要添加3条路由规则，第一条路由规则将PyWebIO应用的视图函数绑定到 ``/io`` 路径下，第二条路由用于提供PyWebIO的前端index.html文件，最后一个路由用于提供PyWebIO的其他静态文件

        启动Django应用后，访问 ``http://localhost/`` 即可打开PyWebIO应用

   .. tab:: aiohttp

      添加两个PyWebIO相关的路由：一个用来提供静态的前端文件，另一个用来和浏览器进行WebSocket通讯::

            from aiohttp import web
            from pywebio.platform.aiohttp import static_routes, webio_handler

            app = web.Application()
            # task_func 为使用PyWebIO编写的任务函数
            app.add_routes([web.get('/io', webio_handler(task_func))])  # http通信接口
            app.add_routes(static_routes('/'))  # 前端静态文件托管

            web.run_app(app, host='localhost', port=8080)

      启动aiohttp应用后，访问 ``http://localhost/`` 即可打开PyWebIO应用

      .. attention::

        当使用aiohttp后端时，PyWebIO使用WebSocket协议和浏览器进行通讯，如果你的aiohttp应用处在反向代理(比如Nginx)之后，
        可能需要特别配置反向代理来支持WebSocket协议，:ref:`这里 <nginx_ws_config>` 有一个Nginx配置WebSocket的例子。

.. _integration_web_framework_note:

注意事项
^^^^^^^^^^^
**PyWebIO静态资源的托管**

在开发阶段，使用后端框架提供的静态文件服务对于开发和调试都十分方便，上文的与Web框架集成的示例代码也都是使用了后端框架提供的静态文件服务。
但出于性能考虑，托管静态文件最好的方式是使用 `反向代理 <https://en.wikipedia.org/wiki/Reverse_proxy>`_ (比如 `nginx <https://nginx.org/>`_ )
或者 `CDN <https://en.wikipedia.org/wiki/Content_delivery_network>`_ 服务。

**前端页面和后端接口的路径约定**

PyWebIO默认通过当前页面的同级的 ``./io`` API与后端进行通讯。

例如你将PyWebIO静态文件托管到 ``/A/B/C/(.*)`` 路径下，那么你需要将PyWebIO API的路由绑定到 ``/A/B/C/io`` 处；
你也可以在PyWebIO应用的地址中添加 ``pywebio_api`` url参数来指定PyWebIO后端API地址，
例如 ``/A/B/C/?pywebio_api=/D/pywebio`` 将PyWebIO后端API地址设置到了 ``/D/pywebio`` 处。

``pywebio_api`` 参数可以使用相对地址、绝对地址，也可以指定其他服务器。

.. caution::

   需要注意 ``pywebio_api`` 参数的格式：

   * 相对地址可以为 ``./xxx/xxx`` 或 ``xxx/xxx`` 的相对地址格式。
   * 绝对地址以 ``/`` 开头，比如 ``/aaa/bbb`` .
   * 指定其他服务器需要使用完整格式: ``http://example.com:5000/aaa/io`` 、 ``ws://example.com:8080/bbb/ws_io`` ,或者省略协议字段: ``//example.com:8080/aaa/io`` 。省略协议字段时，PyWebIO根据当前页面的协议确定要使用的协议: 若当前页面为http协议，则后端接口自动选择http或ws协议；若当前页面为https协议，则后端接口自动选择https或wss协议。

如果你不想自己托管静态文件，你可以使用PyWebIO的Github Page页面: ``https://wang0618.github.io/PyWebIO/pywebio/html/?pywebio_api=`` ，需要在页面上通过 ``pywebio_api`` 参数传入后端API地址，并且将 ``https://wang0618.github.io`` 加入 ``allowed_origins`` 列表中（见下文"跨域配置"说明）。

**跨域配置**

当后端API与前端页面不在同一host下时，需要在 `webio_handler() <pywebio.platform.tornado.webio_handler>` 或
`webio_view() <pywebio.platform.flask.webio_view>` 中使用 ``allowed_origins`` 或 ``check_origin``
参数来使后端接口允许前端页面的请求。

.. _coroutine_based_session:

基于协程的会话
---------------
此部分内容属于高级特性，您不必使用此部分也可以实现PyWebIO支持的全部功能。PyWebIO中所有仅用于协程会话的函数或方法都在文档中有特别说明。

PyWebIO的会话实现默认是基于线程的，用户每打开一个和服务端的会话连接，PyWebIO会启动一个线程来运行任务函数。
除了基于线程的会话，PyWebIO还提供了基于协程的会话。基于协程的会话接受协程函数作为任务函数。

基于协程的会话为单线程模型，所有会话都运行在一个线程内。对于IO密集型的任务，协程比线程占用更少的资源同时又拥有媲美于线程的性能。

使用协程会话
^^^^^^^^^^^^^^^^

要使用基于协程的会话，需要使用 ``async`` 关键字将任务函数声明为协程函数，并使用 ``await`` 语法调用PyWebIO输入函数:

.. code-block:: python
   :emphasize-lines: 5,6

    from pywebio.input import *
    from pywebio.output import *
    from pywebio import start_server

    async def say_hello():
        name = await input("what's your name?")
        put_text('Hello, %s' % name)

    start_server(say_hello, auto_open_webbrowser=True)

在协程任务函数中，也可以使用 ``await`` 调用其他协程或标准库 `asyncio <https://docs.python.org/3/library/asyncio.html>`_ 中的可等待对象( `awaitable objects <https://docs.python.org/3/library/asyncio-task.html#asyncio-awaitables>`_ ):

.. code-block:: python
   :emphasize-lines: 6,10

    import asyncio
    from pywebio import start_server

    async def hello_word():
        put_text('Hello ...')
        await asyncio.sleep(1)  # await asyncio 库中的 awaitable objects
        put_text('... World!')

    async def main():
        await hello_word()  # await 协程
        put_text('Bye, bye')

    start_server(main, auto_open_webbrowser=True)

.. attention::

   在基于协程的会话中， :doc:`pywebio.input </input>` 模块中的定义输入函数都需要使用 ``await`` 语法来获取返回值，
   忘记使用 ``await`` 将会是在使用基于协程的会话时常出现的错误。

   其他在协程会话中也需要使用 ``await`` 语法来进行调用函数有:

    * `pywebio.session.run_asyncio_coroutine(coro_obj) <pywebio.session.run_asyncio_coroutine>`
    * `pywebio.session.eval_js(expression) <pywebio.session.eval_js>`
    * `pywebio.session.hold() <pywebio.session.hold>`

.. warning::

   虽然PyWebIO的协程会话兼容标准库 ``asyncio`` 中的 ``awaitable objects`` ，但 ``asyncio`` 库不兼容PyWebIO协程会话中的 ``awaitable objects`` .

   也就是说，无法将PyWebIO中的 ``awaitable objects`` 传入 ``asyncio`` 中的接受 ``awaitable objects`` 作为参数的函数中，比如如下调用是 **不被支持的** ::

      await asyncio.shield(pywebio.input())
      await asyncio.gather(asyncio.sleep(1), pywebio.session.eval_js('1+1'))
      task = asyncio.create_task(pywebio.input())

协程会话的并发
^^^^^^^^^^^^^^^^

在基于协程的会话中，你可以启动线程，但是无法在其中调用PyWebIO交互函数（ `register_thread() <pywebio.session.register_thread>` 在协程会话中不可用）。
但你可以使用 `run_async(coro) <pywebio.session.run_async>` 来异步执行一个协程对象，新协程内可以使用PyWebIO交互函数::

    from pywebio import start_server
    from pywebio.session import run_async

    async def counter(n):
        for i in range(n):
            put_text(i)
            await asyncio.sleep(1)

    async def main():
        run_async(counter(10))
        put_text('Main coroutine function exited.')


    start_server(main, auto_open_webbrowser=True)

`run_async(coro) <pywebio.session.run_async>` 返回一个 `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` ，通过 `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` 可以查询协程运行状态和关闭协程。

协程会话的关闭
^^^^^^^^^^^^^^^^
与基于线程的会话类似，在基于协程的会话中，当任务函数和在会话内通过 `run_async() <pywebio.session.run_async>` 运行的协程全部结束后，会话关闭。

对于因为用户的关闭浏览器而造成的会话结束，处理逻辑和 :ref:`基于线程的会话 <session_close>` 一致:
此时当前会话内还未返回的PyWebIO输入函数调用将抛出 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常，之后对于PyWebIO交互函数的调用将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` 或 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常。

协程会话也同样支持使用 `defer_call(func) <pywebio.session.defer_call>` 来设置会话结束时需要调用的函数。

协程会话与Web框架集成
^^^^^^^^^^^^^^^^^^^^^^^^^

基于协程的会话同样可以与Web框架进行集成，只需要在原来传入任务函数的地方改为传入协程函数即可。

但当前在使用基于协程的会话集成进Flask或Django时，存在一些限制：

一是协程函数内还无法直接通过 ``await`` 直接等待asyncio库中的协程对象，目前需要使用 `run_asyncio_coroutine() <pywebio.session.run_asyncio_coroutine>` 进行包装。

二是，在启动Flask/Django这类基于线程的服务器之前需要启动一个单独的线程来运行事件循环。

使用基于协程的会话集成进Flask的示例:

.. code-block:: python
   :emphasize-lines: 12,25

    import asyncio
    import threading
    from flask import Flask, send_from_directory
    from pywebio import STATIC_PATH
    from pywebio.output import *
    from pywebio.platform.flask import webio_view
    from pywebio.platform.httpbased import run_event_loop
    from pywebio.session import run_asyncio_coroutine

    async def hello_word():
        put_text('Hello ...')
        await run_asyncio_coroutine(asyncio.sleep(1))  # 无法直接 await asyncio.sleep(1)
        put_text('... World!')

    app = Flask(__name__)
    app.add_url_rule('/io', 'webio_view', webio_view(hello_word),
                                methods=['GET', 'POST', 'OPTIONS'])

    @app.route('/')
    @app.route('/<path:static_file>')
    def serve_static_file(static_file='index.html'):
        return send_from_directory(STATIC_PATH, static_file)

    # 事件循环线程
    threading.Thread(target=run_event_loop, daemon=True).start()
    app.run(host='localhost', port='80')

最后，使用PyWebIO编写的协程函数不支持Script模式，总是需要使用 ``start_server`` 来启动一个服务或者集成进Web框架来调用。