User's guide
============

如果你接触过Web开发，你可能对接下来描述的PyWebIO的用法感到不太习惯，不同于传统Web开发的后端实现接口、前端进行展示交互的模式，在PyWebIO中，所有的逻辑都通过编写Python代码实现。

事实上，PyWebIO应用的编写逻辑更像控制台程序，只不过这里的终端变成了浏览器。通过PyWebIO提供的命令式API，
你可以简单地调用 ``put_text`` 、 ``put_image`` 、 ``put_table`` 等函数输出文本、图片、表格等内容到浏览器，也可以调用 ``input`` 、 ``select`` 、
``file_upload`` 等函数在浏览器上显示不同表单来接收用户的输入。此外PyWebIO中还提供了点击事件、布局等支持，让你可以使用最少的代码完成与用户的交互，
并尽可能提供良好的用户体验。

本篇使用指南从几个方面对PyWebIO的使用进行介绍，覆盖了PyWebIO的绝大部分特性。本文档中大部分示例代码的右上方都有一个Demo链接，点击后可以在线预览代码的运行效果。

If you are familiar with web development, you may not be accustomed to the usage of PyWebIO described next, which is different from the traditional web development mode that backend implement api and frontend display content. In PyWebIO, you only need write code in Python.

In fact, the way of writing PyWebIO applications is more like writing a console program, except that the terminal here becomes a browser. Using the imperative API provided by PyWebIO,
you can simply call ``put_text``, ``put_image``, ``put_table`` and other functions to output text, pictures, tables and other content to the browser, or you can call some functions such as ``input``, ``select``, ``file_upload`` to display different forms on the browser to get user input. In addition, PyWebIO also provides support for click events, layout, etc. PyWebIO aims to allow you to use the least code to complete the interaction with the user and provide a good user experience as much as possible.

This user guide introduces you the most of the features of PyWebIO. There is a demo link at the top right of the most of the example codes in this document, where you can preview the running effect of the code online.

Input
------------

输入函数都定义在 :doc:`pywebio.input </input>` 模块中，可以使用 ``from pywebio.input import *`` 引入。

调用输入函数会在浏览器上弹出一个输入表单来获取输入。PyWebIO的输入函数是阻塞式的（和Python内置的 `input` 一样），在表单被成功提交之前，输入函数不会返回。

The input functions are defined in the :doc:`pywebio.input </input>` module and can be imported using ``from pywebio.input import *``.

Calling the input function will pop up an input form on the browser. PyWebIO's input functions is blocking (same as Python's built-in ``input()`` function) and will not return until the form is successfully submitted.

Basic input
^^^^^^^^^^^^^

Here are some basic types of input.

Text input:

.. exportable-codeblock::
    :name: text-input
    :summary: Text input

    age = input("How old are you?", type=NUMBER)
    put_text('age = %r' % age)  # ..demo-only

After running the above code, the browser will pop up a text input box to get the input. After the user completes the input and submits the form, the function returns the value entered by the user.

Here are some other types of input functions:

.. exportable-codeblock::
    :name: basic-input
    :summary: Basic input

    # Password input
    password = input("Input password", type=PASSWORD)
    put_text('password = %r' % password)  # ..demo-only
    ## ----

    # Drop-down selection
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    put_text('gift = %r' % gift)  # ..demo-only
    ## ----

    # Checkbox
    agree = checkbox("User Term", options=['I agree to terms and conditions'])
    put_text('agree = %r' % agree)  # ..demo-only
    ## ----

    # Single choice
    answer = radio("Choose one", options=['A', 'B', 'C', 'D'])
    put_text('answer = %r' % answer)  # ..demo-only
    ## ----

    # Multi-line text input
    text = textarea('Text Area', rows=3, placeholder='Some text')
    put_text('text = %r' % text)  # ..demo-only
    ## ----

    # File Upload
    img = file_upload("Select a image:", accept="image/*")
    if img:    # ..demo-only
        put_image(img['content'], title=img['filename'])  # ..demo-only


Parameter of input functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

输入函数可指定的参数非常丰富（全部参数及含义请见 :doc:`函数文档 </input>` ）:

There are many parameters that can be passed to the input function(for complete parameters, please refer to the :doc:`function document </input>`):

.. exportable-codeblock::
    :name: input-args
    :summary: Parameter of input functions

    input('This is label', type=TEXT, placeholder='This is placeholder',
            help_text='This is help text', required=True)

以上代码将在浏览器上显示如下：

The results of the above example are as follows:

.. image:: /assets/input_1.png

我们可以为输入指定校验函数，校验函数应在校验通过时返回None，否则返回错误消息:

You can specify a validation function for the input by using ``validate`` parameter. The validation function should return ``None`` when the check passes, otherwise an error message will be returned:

.. exportable-codeblock::
    :name: input-valid-func
    :summary: Input validate function for

    def check_age(p):  # return None when the check passes, otherwise an error message will be returned
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = input("How old are you?", type=NUMBER, validate=check_age)
    put_text('age = %r' % age)  # ..demo-only

当用户输入了不合法的值时，页面上的显示如下:

When the user input an illegal value, the display on the page is as follows:

.. image:: /assets/input_2.png


:func:`pywebio.input.textarea` 还支持使用 `Codemirror <https://codemirror.net/>`_ 实现代码风格的编辑区，只需使用 ``code`` 参数传入Codemirror支持的选项即可(最简单的情况是直接传入 ``code={}`` 或 ``code=True``):

:func:`pywebio.input.textarea` supports for code editing by using `Codemirror <https://codemirror.net/>`_ , just use the ``code`` parameter to pass in the options supported by Codemirror (the simplest case is to pass in ``code={}`` or ``code=True`` directly):

You can use ``code`` parameter in :func:`pywebio.input.textarea` to make a code editing textarea. This feature uses `Codemirror <https://codemirror.net/>`_ as underlying implementation. The ``code`` parameter accept the Codemirror options as a dict.

.. exportable-codeblock::
    :name: codemirror
    :summary: Code editing by using textarea

    code = textarea('Code Edit', code={
        'mode': "python",  # code language
        'theme': 'darcula',  # Codemirror theme. Visit https://codemirror.net/demo/theme.html#cobalt to get more themes
    }, value='import something\n# Write your python code')
    put_code(code, language='python')  # ..demo-only

文本框的显示效果为：

The results of the above example are as follows:

.. image:: /assets/codemirror_textarea.png

:ref:`这里 <codemirror_options>` 列举了一些常用的Codemirror选项，完整的Codemirror选项请见：https://codemirror.net/doc/manual.html#config

:ref:`Here <codemirror_options>` are some commonly used Codemirror options. For complete Codemirror options, please visit: https://codemirror.net/doc/manual.html#config

Input Group
^^^^^^^^^^^^^

PyWebIO支持输入组, 返回结果为一个字典。`pywebio.input.input_group()` 接受单项输入组成的列表作为参数, 返回以单项输入函数中的 ``name`` 作为键、以输入数据为值的字典:

PyWebIO uses input group to get multiple inputs in single form. `pywebio.input.input_group()` accepts a list of single input function call as parameter, and returns a dictionary with the ``name`` from the single input function as the key and the input data as the value:


.. exportable-codeblock::
    :name: input-group
    :summary: Input Group

    def check_age(p):  # ..demo-only
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

The input group also supports using ``validate`` parameter to set the validation function, which accepts the entire form data as parameter:

.. exportable-codeblock::
    :name: input-group
    :summary: 输入组

    def check_age(p):  # single input item validation  # ..demo-only
        if p < 10:                  # ..demo-only
            return 'Too young!!'    # ..demo-only
        if p > 60:                  # ..demo-only
            return 'Too old!!'      # ..demo-only
                                    # ..demo-only
    def check_form(data):  # input group validation: return (input name, error msg) when validation error
        if len(data['name']) > 6:
            return ('name', 'Name too long!')
        if data['age'] <= 0:
            return ('age', 'Age can not be negative!')

    data = input_group("Basic info",[           # ..demo-only
       input('Input your name', name='name'),   # ..demo-only
       input('Input your age', name='age', type=NUMBER, validate=check_age)  # ..demo-only
    ], validate=check_form)              # ..demo-only
    put_text(data['name'], data['age'])    # ..demo-only

.. attention::
   PyWebIO 根据是否在输入函数中传入 ``name`` 参数来判断输入函数是在 `input_group` 中还是被单独调用。
   所以当单独调用一个输入函数时, **不要** 设置 ``name`` 参数；而在 `input_group` 中调用输入函数时，需 **务必提供** ``name`` 参数

   PyWebIO determine whether the input function is in `input_group` or is called alone according to whether the ``name`` parameter is passed. So when calling an input function alone, **do not** set the ``name`` parameter; when calling the input function in `input_group`, you **must** provide the ``name`` parameter.

Output
------------

输出函数都定义在 :doc:`pywebio.output </output>` 模块中，可以使用 ``from pywebio.output import *`` 引入。

The output functions are all defined in the :doc:`pywebio.output </output>` module and can be imported using ``from pywebio.output import *``.

When output functions is called, the content will be output to the browser in real time. The output functions can be called at any time during the application life cycle.

Basic Output
^^^^^^^^^^^^^^

PyWebIO提供了一系列函数来输出表格、链接等格式:

PyWebIO provides a series of functions to output text, tables, links, etc:

.. exportable-codeblock::
    :name: basic-output
    :summary: Basic Output

    # Text Output
    put_text("Hello world!")
    ## ----

    # Table Output
    put_table([
        ['Commodity', 'Price'],
        ['Apple', '5.5'],
        ['Banana', '7'],
    ])
    ## ----

    # Markdown Output
    put_markdown('~~Strikethrough~~')
    ## ----

    # File Output
    put_file('hello_word.txt', b'hello word!')
    ## ----

    # PopUp Output
    popup('popup title', 'popup text content')


PyWebIO提供的全部输出函数见 :doc:`pywebio.output </output>` 模块。另外，PyWebIO还支持一些第三方库来进行数据可视化，参见 :doc:`第三方库生态 </libraries_support>` 。

For all output functions provided by PyWebIO, please refer to the :doc:`pywebio.output </output>` module. In addition, PyWebIO also supports data visualization with some third-party libraries, see :doc:`Third-party library ecology </libraries_support>`.

.. _combine_output:

Combined Output(组合输出)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
函数名以 ``put_`` 开始的输出函数，可以与一些输出函数组合使用，作为最终输出的一部分：

The output function whose function name starts with ``put_`` can be combined with some output functions as part of the final output:

`put_table() <pywebio.output.put_table>` 支持以 ``put_xxx()`` 调用作为单元格内容:

You can pass ``put_xxx()`` calls to `put_table() <pywebio.output.put_table>` as cell content:

.. exportable-codeblock::
    :name: putxxx
    :summary: Combined output

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

The results of the above example are as follows:

.. image:: /assets/put_table.png

类似地， `popup() <pywebio.output.popup>` 也可以将 ``put_xxx()`` 调用作为弹窗内容:

Similarly, you can pass ``put_xxx()`` calls to `popup() <pywebio.output.popup>` as the popup content:

.. exportable-codeblock::
    :name: popup
    :summary: Popup

    popup('Popup title', [
        put_html('<h3>Popup Content</h3>'),
        'plain html: <br/>',  # Equivalent to: put_text('plain html: <br/>')
        put_table([['A', 'B'], ['C', 'D']]),
        put_buttons(['close_popup()'], onclick=lambda _: close_popup())
    ])

其他接受 ``put_xxx()`` 调用作为参数的输出函数还有 `put_collapse() <pywebio.output.put_collapse>` 、 `put_scrollable() <pywebio.output.put_scrollable>` 、`put_row() <pywebio.output.put_row>` 等,
此外，还可以通过 `put_widget() <pywebio.output.put_widget>` 自定义可接收 ``put_xxx()`` 调用的输出组件，具体用法请参考函数文档。

Other output functions that accept ``put_xxx()`` calls as parameters are `put_collapse() <pywebio.output.put_collapse>`, `put_scrollable() <pywebio.output.put_scrollable>`, `put_row() <pywebio.output.put_row>`, etc. In addition, you can use `put_widget() <pywebio.output.put_widget>` to make your own output widgets that can accept ``put_xxx()`` calls. For more information, please refer to corresponding function documentation.

使用组合输出时，如果想在内容输出后，对其中的 ``put_xxx()`` 子项进行动态修改，可以使用 `output() <pywebio.output.output>` 函数，
`output() <pywebio.output.output>` 就像一个占位符，它可以像 ``put_xxx()`` 一样传入 `put_table` 、 `popup` 、 `put_widget` 等函数中作为输出的一部分，
并且，在输出后，还可以对其中的内容进行修改(比如重置或增加内容):

When using combined output, if you want to dynamically update the ``put_xxx()`` content after it has been output, you can use the `output() <pywebio.output.output>` function. `output() <pywebio.output.output>` is like a placeholder, it can be passed in anywhere that ``put_xxx()`` can passed in. And after being output, the content can also be modified:

.. exportable-codeblock::
    :name: output
    :summary: Output placeholder——`output()`

    hobby = output(put_text('Coding'))
    put_table([
       ['Name', 'Hobbies'],
       ['Wang', hobby]      # hobby is initialized to Coding
    ])
    ## ----

    hobby.reset(put_text('Movie'))  # hobby is reset to Movie
    ## ----
    hobby.append(put_text('Music'), put_text('Drama'))   # append Music, Drama to hobby
    ## ----
    hobby.insert(0, put_markdown('**Coding**'))  # insert the Coding into the top of the hobby


Callback
^^^^^^^^^^^^^^

从上面可以看出，PyWebIO把交互分成了输入和输出两部分：输入函数为阻塞式调用，会在用户浏览器上显示一个表单，在用户提交表单之前输入函数将不会返回；输出函数将内容实时输出至浏览器。这种交互方式和控制台程序是一致的，因此PyWebIO应用非常适合使用控制台程序的编写逻辑来进行开发。

As we can see from the above, PyWebIO divides the interaction into two parts: input and output. The input function is blocking, a form will be displayed on the user's web browser when calling input function, the input function will not return util the user submits the form. The output function is used to output content to the browser in real time. This input and output behavior is consistent with the console program. That's why we say PyWebIO turning the browser into a "rich text terminal". So you can write PyWebIO applications in script programing way.

此外，PyWebIO还支持事件回调：PyWebIO允许你输出一些控件，当控件被点击时执行提供的回调函数。

In addition, PyWebIO also supports event callbacks: PyWebIO allows you to output some buttons and the provided callback function will be executed when button is clicked.

This is an example:

.. exportable-codeblock::
    :name: onclick-callback
    :summary: Event callback

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

The call to `put_table() <pywebio.output.put_table>` will not block. When user clicks a button, the corresponding callback function will be called:

.. image:: /assets/table_onclick.*

当然，PyWebIO还支持单独的按钮控件:

PyWebIO also supports output button alone:

.. exportable-codeblock::
    :name: put-buttons
    :summary: 按钮控件

    def btn_click(btn_val):
        put_text("You click %s button" % btn_val)
    put_buttons(['A', 'B', 'C'], onclick=btn_click)

.. note::
   在PyWebIO会话(关于会话的概念见下文 :ref:`Server与script模式 <server_and_script_mode>` )结束后，事件回调也将不起作用，你可以在任务函数末尾处使用 :func:`pywebio.session.hold()` 函数来将会话保持，这样在用户关闭浏览器页面前，事件回调将一直可用。

   After the PyWebIO session (see :ref:`Server and script mode <server_and_script_mode>` for more information about session) closed, the event callback will not work. You can call the :func:`pywebio.session.hold()` function at the end of the task function to hold the session, so that the event callback will always be available before the browser page is closed by user.

Output Scope
^^^^^^^^^^^^^^
PyWebIO使用Scope模型来对内容输出的位置进行灵活地控制，PyWebIO的内容输出区可以划分出不同的输出域，PyWebIO将输出域称作 `Scope` 。

PyWebIO uses the scope model to give more control to the location of content output. The output area of PyWebIO can be divided into different output domains. The output domain is called Scope in PyWebIO.

输出域为输出内容的容器，各个输出域之间上下排列，输出域也可以进行嵌套。

The output domain is a container for output content, and each output domain is arranged vertically, and the output domains can also be nested.

每个输出函数（函数名形如 `put_xxx()` ）都会将内容输出到一个Scope，默认为"当前Scope"，"当前Scope"由运行时上下文确定，输出函数也可以手动指定输出到的Scope。Scope名在会话内唯一。

Each output function (function name like ``put_xxx()``) will output the content to a scope, the default is "current scope". "current scope" is determined by the runtime context. The output function can also manually specify the scope to be output to. The scope name is unique within the session.

.. _use_scope:

**use_scope()**

可以使用 `use_scope() <pywebio.output.use_scope>` 开启并进入一个新的输出域，或进入一个已经存在的输出域:

You can use `use_scope() <pywebio.output.use_scope>` to open and enter a new output scope, or enter an existing output scope:

.. exportable-codeblock::
    :name: use-scope
    :summary: use `use_scope()` to open or enter scope

    with use_scope('scope1'):  # open and enter a new output: 'scope1'
        put_text('text1 in scope1')

    put_text('text in parent scope of scope1')

    with use_scope('scope1'):  # enter an existing output scope: 'scope1'
        put_text('text2 in scope1')

以上代码将会输出:

The results of the above code are as follows::

    text1 in scope1
    text2 in scope1
    text in parent scope of scope1

`use_scope() <pywebio.output.use_scope>` 还可以使用 `clear` 参数将scope中原有的内容清空:

You can use ``clear`` parameter in `use_scope() <pywebio.output.use_scope>` to clear the previous content in the scope:

.. exportable-codeblock::
    :name: use-scope
    :summary: `use_scope()`'s `clear` parameter

    with use_scope('scope2'):
        put_text('create scope2')

    put_text('text in parent scope of scope2')
    ## ----

    with use_scope('scope2', clear=True):  # enter an existing output scope and clear the original content
        put_text('text in scope2')

以上代码将会输出:

The results of the above code are as follows::

    text in scope2
    text in parent scope of scope2

`use_scope() <pywebio.output.use_scope>` 还可以作为装饰器来使用:

`use_scope() <pywebio.output.use_scope>` can also be used as a decorator:

.. exportable-codeblock::
    :name: use-scope-decorator
    :summary: `use_scope()` as decorator

    import time  # ..demo-only
    from datetime import datetime

    @use_scope('time', clear=True)
    def show_time():
        put_text(datetime.now())

    while 1:          # ..demo-only
       show_time()    # ..demo-only
       time.sleep(1)  # ..demo-only

第一次调用 ``show_time`` 时，将会在当前位置创建 ``time`` 输出域并在其中输出当前时间，之后每次调用 ``show_time()`` ，时间都会输出到相同的区域。

When calling ``show_time()`` for the first time, a ``time`` scope will be created at the current position and the current time will be output to it, and then every time the ``show_time()`` is called, the time will be output to the same area.

Scope是可嵌套的，初始条件下，PyWebIO应用只有一个最顶层的 ``ROOT`` Scope。每创建一个新Scope，Scope的嵌套层级便会多加一层，每退出当前Scope，Scope的嵌套层级便会减少一层。
PyWebIO使用Scope栈来保存运行时的Scope的嵌套层级。

Scopes can be nested. At the beginning, PyWebIO applications have only one ``ROOT`` Scope. Each time a new scope is created, the nesting level of the scope will increase by one level, and each time the current scope is exited, the nesting level of the scope will be reduced by one. PyWebIO uses the Scope stack to save the nesting level of scope at runtime.

例如，如下代码将会创建3个Scope:

For example, the following code will create 3 scopes:

.. exportable-codeblock::
    :name: use-scope-nested
    :summary: Nested Scope

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


以上代码将会产生如下Scope布局:

The above code will make the following Scope layout::

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

**Scope related parameters of output function**

输出函数（函数名形如 ``put_xxx()`` ）在默认情况下，会将内容输出到"当前Scope"，可以通过 ``use_scope()`` 设置运行时上下文的"当前Scope"。

The output function (function name like ``put_xxx()``) will output the content to the "current scope" by default, and the "current scope" of the runtime context can be set by use_scope().

此外，也可以通过输出函数的 ``scope`` 参数指定输出的目的Scope:

In addition, you can use the ``scope`` parameter of the output function to specify the destination scope to output:

.. exportable-codeblock::
    :name: put-xxx-scope
    :summary: ``scope`` parameter of the output function

    with use_scope('scope3'):
        put_text('text1 in scope3')   # output to scope3
        put_text('text in ROOT scope', scope='ROOT')   # output to ROOT Scope

    put_text('text2 in scope3', scope='scope3')   # output to scope3

以上将会输出:

The results of the above code are as follows::

    text1 in scope3
    text2 in scope3
    text in ROOT scope

``scope`` 参数除了直接指定目标Scope名，还可以使用一个整形通过索引Scope栈来确定Scope：0表示最顶层也就是ROOT Scope，-1表示当前Scope，-2表示进入当前Scope前所使用的Scope，......

In addition to directly specifying the target scope name, the ``scope`` parameter can also accept an integer to determine the scope by indexing the scope stack: 0 means the top level scope(the ROOT Scope), -1 means the current Scope, -2 means the scope used before entering the current scope, ...

默认条件下，在同一Scope中的输出内容，会根据输出函数的调用顺序从上往下排列，最后调用的输出函数会输出内容到目标Scope的底部。通过输出函数的 ``position`` 参数可以将输出内容插入到目标Scope的其他位置。

By default, the output content in the same scope will be arranged from top to bottom according to the calling order of the output function, and the output function called last will output the content to the bottom of the target scope. The output content can be inserted into other positions of the target scope by using the ``position`` parameter of the output function.

一个Scope中各次输出的元素具有像数组一样的索引，最前面的编号为0，以此往后递增加一；同样可以使用负数对Scope中的元素进行索引，-1表示最后面的元素，-2表示次后面的元素......

Each output element in a scope has an index like Python list, the first element's index is 0, and the next element's index is incremented by one. You can also use a negative number to index the elements in the scope, -1 means the last element, -2 means the element before the last...

``position`` 参数类型为整形， ``position>=0`` 时表示输出内容到目标Scope的第position号元素的前面； ``position<0`` 时表示输出内容到目标Scope第position号元素之后:

The ``position`` parameter is integer. When ``position>=0``, it means to insert content before the element whose index equal ``position``; when ``position<0``, it means to insert content after the element whose index equal ``position``:

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

**Scope control**

除了 `use_scope()` , PyWebIO同样提供了以下scope控制函数：

In addition to `use_scope() <pywebio.output.use_scope>`, PyWebIO also provides the following scope control functions:

* `set_scope(name) <pywebio.output.set_scope>` : Create scope at current location(or specified location)
* `clear(scope) <pywebio.output.clear>` : Clear the contents of the scope
* `remove(scope) <pywebio.output.remove>` : Remove scope
* `scroll_to(scope) <pywebio.output.scroll_to>` : Scroll the page to the scope


Page environment settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Page Title**

You can call `set_env(title=...) <pywebio.session.set_env>` to set the page title。

**Auto Scroll**

在进行一些持续性的输出时(比如日志输出)，有时希望在有新输出后自动将页面滚动到最下方，这时可以调用 `set_env(auto_scroll_bottom=True) <pywebio.session.set_env>` 来开启自动滚动。
注意，开启后，只有输出到ROOT Scope才可以触发自动滚动。

When performing some continuous output (such as log output), you may want to automatically scroll the page to the bottom when there is new output. You can call `set_env(auto_scroll_bottom=True) <pywebio.session.set_env>` to enable automatic scrolling. Note that after enabled, only outputting to ROOT scope can trigger automatic scrolling.

**Output Animation**

PyWebIO在输出内容时默认会使用淡入的动画效果来显示内容，可使用 `set_env(output_animation=False) <pywebio.session.set_env>` 来关闭动画。

PyWebIO will use the fade-in animation effect to display the content by default. You can use `set_env(output_animation=False) <pywebio.session.set_env>` to turn off the animation.

有关不同环境配置的效果可查看 :demo_host:`set_env Demo </?pywebio_api=set_env_demo>`

For the effects of different environment settings, please see :demo_host:`set_env Demo </?pywebio_api=set_env_demo>`

Layout
^^^^^^^^^^^^^^
一般情况下，使用上文介绍的各种输出函数足以完成各种内容的展示，但直接调用输出函数产生的输出之间都是竖直排列的，如果想实现更复杂的布局（比如在页面左侧显示一个代码块，在右侧显示一个图像），就需要借助布局函数。

In general, using the various output functions introduced above to output all kinds of content is enough, but these outputs are arranged vertically. If you want to make a more complex layout (such as displaying a code block on the left side of the page and an image on the right left), you need to use layout functions.

``pywebio.output`` 模块提供了3个布局函数，通过对他们进行组合可以完成各种复杂的布局:

The ``pywebio.output`` module provides three layout functions, and you can make complex layouts by combining them:

* `put_row() <pywebio.output.put_row>` : 使用行布局输出内容. 内容在水平方向上排列 Use row layout to output content. The content is arranged horizontally
* `put_column() <pywebio.output.put_column>` : 使用列布局输出内容. 内容在竖直方向上排列 Use column layout to output content. The content is arranged vertically
* `put_grid() <pywebio.output.put_grid>` : 使用网格布局输出内容 Output content using grid layout

通过组合 ``put_row()`` 和 ``put_column()`` 可以实现灵活布局:

Here is a layout example by combining ``put_row()`` and ``put_column()``:

.. exportable-codeblock::
    :name: put-row-column
    :summary: Layout functions

    put_row([
        put_column([
            put_code('A'),
            put_row([
                put_code('B1'), None,  # None represents the space between the output
                put_code('B2'), None,
                put_code('B3'),
            ]),
            put_code('C'),
        ]), None,
        put_code('D'), None,
        put_code('E')
    ])

显示效果如下:

The results of the above example are as follows:

.. image:: /assets/layout.png
   :align: center

布局函数还支持自定义各部分的尺寸:

The layout function also supports customizing the size of each part::

    put_row([put_image(...), put_image(...)], size='40% 60%')  # The ratio of the width of two images is 2:3

更多布局函数的用法及代码示例请查阅 :ref:`布局函数文档 <style_and_layout>` .

For more information, please refer to the :ref:`layout function documentation <style_and_layout>`.

Style
^^^^^^^^^^^^^^
如果你熟悉 `CSS样式 <https://www.google.com/search?q=CSS%E6%A0%B7%E5%BC%8F>`_ ，你还可以使用 `style() <pywebio.output.style>` 函数给输出设定自定义样式。

If you are familiar with `CSS <https://en.wikipedia.org/wiki/CSS>`_ styles, you can use the `style() <pywebio.output.style>` function to set a custom style for the output.

可以给单个的 ``put_xxx()`` 输出设定CSS样式，也可以配合组合输出使用:

You can set the CSS style for a single ``put_xxx()`` output:

.. exportable-codeblock::
    :name: style
    :summary: style of output

    style(put_text('Red'), 'color: red')

    ## ----
    put_table([
        ['A', 'B'],
        ['C', style(put_text('Red'), 'color: red')],
    ])

``style()`` 也接受列表作为输入，``style()`` 会为列表的每一项都设置CSS样式，返回值可以直接输出，可用于任何接受 ``put_xxx()`` 列表的地方:

`style() <pywebio.output.style>` also accepts a list of output calls, `style() <pywebio.output.style>` will set the CSS style for each item in the list:

.. exportable-codeblock::
    :name: style-list
    :summary: style a list of output

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

Server mode and Script mode
------------------------------------

在 :ref:`Hello, world <hello_word>` 一节中，已经知道，PyWebIO支持在普通的脚本中调用和使用
`start_server() <pywebio.platform.tornado.start_server>` 启动一个Web服务两种模式。

In the :ref:`Hello, world <hello_word>` section, we already know that PyWebIO supports two modes of running as a script and  using `start_server() <pywebio.platform.tornado.start_server>` to run as a web service.

**Server mode**

在Server模式下，PyWebIO会启动一个Web服务来持续性地提供服务。需要提供一个任务函数(类似于Web开发中的视图函数)，当用户访问服务地址时，PyWebIO会开启一个新会话并运行任务函数。

In Server mode, PyWebIO will start a web server to continuously provide services. A task function (similar to the view function in Flask) needs to be provided. When the user accesses the service address, PyWebIO will open a new session and run the task function.

使用 `start_server() <pywebio.platform.tornado.start_server>` 来启动PyWebIO的Server模式， `start_server() <pywebio.platform.tornado.start_server>` 除了接收一个函数作为任务函数外，
还支持传入函数列表或字典，从而使一个PyWebIO Server下可以有多个不同功能的服务，服务之间可以通过 `go_app() <pywebio.session.go_app>` 或 `put_link() <pywebio.output.put_link>` 进行跳转

Use `start_server() <pywebio.platform.tornado.start_server>` to start a web service. In addition to accepting a function as task function, ``start_server()`` also accepts a list of task function or a dictionary of it, so that a PyWebIO Server can have multiple services with different functions. You can use `go_app() <pywebio.session.go_app>` or `put_link() <pywebio.output.put_link>` to jump between services::

    def task_1():
        put_text('task_1')
        put_buttons(['Go task 2'], [lambda: go_app('task_2')])
        hold()

    def task_2():
        put_text('task_2')
        put_buttons(['Go task 1'], [lambda: go_app('task_1')])
        hold()

    def index():
        put_link('Go task 1', app='task_1')  # Use `app` parameter to specify the task name
        put_link('Go task 2', app='task_2')

    start_server([index, task_1, task_2])  # or start_server({'index': index, 'task_1': task_1, 'task_2': task_2}) For more information, please refer to the function documentation.

.. attention::

    注意，在Server模式下，仅能在任务函数上下文中对PyWebIO的交互函数进行调用。比如如下调用是 **不被允许的**

    Note that in Server mode, PyWebIO's input and output functions can only be called in the context of task functions. For example, the following code is not allowed::

        import pywebio
        from pywebio.input import input

        port = input('Input port number:')   # ❌ error
        pywebio.start_server(my_task_func, port=int(port))


**Script mode**

Script模式下，在任何位置都可以调用PyWebIO的交互函数。

In Script mode, PyWebIO input and output functions can be called anywhere.

如果用户在会话结束之前关闭了浏览器，那么之后会话内对于PyWebIO交互函数的调用将会引发一个 `SessionException <pywebio.exceptions.SessionException>` 异常。

If the user closes the browser before the end of the session, then calls to PyWebIO input and output functions in the session will cause a `SessionException <pywebio.exceptions.SessionException>` exception.

.. _thread_in_server_mode:

Concurrent
^^^^^^^^^^^^^^

PyWebIO 支持在多线程环境中使用。

PyWebIO can be used in a multi-threading environment.

**Script mode**

在 Script模式下，你可以自由地启动线程，并在其中调用PyWebIO的交互函数。当所有非 `Daemon线程 <https://docs.python.org/3/library/threading.html#thread-objects>`_ 运行结束后，脚本退出。

In Script mode, you can freely start new thread and call PyWebIO interactive functions in it. When all `non-daemonic <https://docs.python.org/3/library/threading.html#thread-objects>`_ threads finish running, the script exits.

**Server mode**

Server模式下，如果需要在新创建的线程中使用PyWebIO的交互函数，需要手动调用 `register_thread(thread) <pywebio.session.register_thread>` 对新进程进行注册（这样PyWebIO才能知道新创建的线程属于哪个会话）。
如果新创建的线程中没有使用到PyWebIO的交互函数，则无需注册。没有使用 `register_thread(thread) <pywebio.session.register_thread>` 注册的线程不受会话管理，其调用PyWebIO的交互函数将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` 异常。
当会话的任务函数和会话内通过 `register_thread(thread) <pywebio.session.register_thread>` 注册的线程都结束运行时，会话关闭。

In Server mode, if you need to use PyWebIO interactive functions in new thread, you need to use `register_thread(thread) <pywebio.session.register_thread>` to register the new thread (so that PyWebIO can know which session the thread belongs to). If the PyWebIO interactive function is not used in the new thread, no registration is required. Threads that are not registered with `register_thread(thread) <pywebio.session.register_thread>` calling PyWebIO's interactive functions will cause `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>`. When both the task function of the session and the thread registered through `register_thread(thread) <pywebio.session.register_thread>` in the session have finished running, the session is closed.

Server模式下多线程的使用示例:

Example of using multi-threading in Server mode::

   def show_time():
       while True:
           with use_scope(name='time', clear=True):
               put_text(datetime.datetime.now())
               time.sleep(1)

   def app():
       t = threading.Thread(target=show_time)
       register_thread(t)
       put_markdown('## Clock')
       t.start()  # run `show_time()` in background

       # ❌ this thread will cause `SessionNotFoundException`
       threading.Thread(target=show_time).start()

       put_text('Background task started.')


   start_server(app, port=8080, debug=True)


.. _session_close:

Close of session
^^^^^^^^^^^^^^^^^

会话还会因为用户的关闭浏览器而结束，这时当前会话内还未返回的PyWebIO输入函数调用将抛出 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常，之后对于PyWebIO交互函数的调用将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` 或 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常。

The session will also close because the user closes the browser page. After the browser page closed, PyWebIO input function calls that have not yet returned in the current session will cause `SessionClosedException <pywebio.exceptions.SessionClosedException>`, and subsequent calls to PyWebIO interactive functions will cause `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` or `SessionClosedException <pywebio.exceptions.SessionClosedException>`.

可以使用 `defer_call(func) <pywebio.session.defer_call>` 来设置会话结束时需要调用的函数。无论是因为用户主动关闭页面还是任务结束使得会话关闭，设置的函数都会被执行。
`defer_call(func) <pywebio.session.defer_call>` 可以用于资源清理等工作。在会话中可以多次调用 `defer_call() <pywebio.session.defer_call>` ,会话结束后将会顺序执行设置的函数。

You can use `defer_call(func) <pywebio.session.defer_call>` to set the function to be called when the session closes. Whether it is because the user closes the page or the task finishes to cause session closed, the function set by `defer_call(func) <pywebio.session.defer_call>` will be executed. `defer_call(func) <pywebio.session.defer_call>` can be used for resource cleaning. You can call `defer_call(func) <pywebio.session.defer_call>` multiple times in the session, and the set functions will be executed sequentially after the session closes.

Integration with web framework
---------------------------------

.. _integration_web_framework:

可以将PyWebIO应用集成到现有的Python Web项目中，PyWebIO应用与Web项目共用一个Web框架。目前支持与Flask、Tornado、Django和aiohttp Web框架的集成。

The PyWebIO application can be integrated into an existing Python Web project, and the PyWebIO application and the Web project share a web framework. PyWebIO currently supports integration with Flask, Tornado, Django and aiohttp web frameworks.

与Web框架集成需要完成两部分配置：托管PyWebIO前端静态文件；暴露PyWebIO后端接口。这其中需要注意前端页面和后端接口的路径约定，
以及前端静态文件与后端接口分开部署时因为跨域而需要的特别设置。

Integration with the web framework basically requires two steps: hosting the PyWebIO frontend static files; exposing the PyWebIO backend API.

Integration method
^^^^^^^^^^^^^^^^^^^^^

不同Web框架的集成方法如下：

The integration methods of different web frameworks are as follows:

.. tabs::

   .. tab:: Tornado

        需要在Tornado应用中引入两个 ``RequestHandler`` ,
        一个 ``RequestHandler`` 用来提供前端静态文件，另一个 ``RequestHandler`` 用来和浏览器进行WebSocket通讯

        Need to add two ``RequestHandler`` to Tornado application,
         One ``RequestHandler`` is used to serve frontend static files, and the other ``RequestHandler`` is the backend API which is used to communicate with the browser through WebSocket::

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
                    (r"/tool/io", webio_handler(task_func)),  # `task_func` is PyWebIO task function
                    (r"/tool/(.*)", tornado.web.StaticFileHandler,
                          {"path": STATIC_PATH, 'default_filename': 'index.html'})  # static files serving
                ])
                application.listen(port=80, address='localhost')
                tornado.ioloop.IOLoop.current().start()

        以上代码调用 `webio_handler(task_func) <pywebio.platform.tornado.webio_handler>` 来获得PyWebIO和浏览器进行通讯的Tornado `WebSocketHandler <https://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketHandler>`_ ，
        并将其绑定在 ``/tool/io`` 路径下；同时将PyWebIO的静态文件使用 `tornado.web.StaticFileHandler <https://www.tornadoweb.org/en/stable/web.html?highlight=StaticFileHandler#tornado.web.StaticFileHandler>`_ 托管到 ``/tool/(.*)`` 路径下。
        启动Tornado服务器后，访问 ``http://localhost/tool/`` 即可打开PyWebIO应用

        In above code, we use `webio_handler(task_func) <pywebio.platform.tornado.webio_handler>` to get the Tornado `WebSocketHandler <https://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketHandler>`_  that communicates with the browser, and bind it to the ``/tool/io`` path. PyWebIO static files are hosted to ``/tool/(.*)`` by using `tornado.web.StaticFileHandler <https://www.tornadoweb.org/en/stable/web.html?highlight=StaticFileHandler#tornado.web.StaticFileHandler>`_ . After starting the Tornado server, you can visit ``http://localhost/tool/`` to open the PyWebIO application.

        .. attention::

           当使用Tornado后端时，PyWebIO使用WebSocket协议和浏览器进行通讯，如果你的Tornado应用处在反向代理(比如Nginx)之后，
           可能需要特别配置反向代理来支持WebSocket协议，:ref:`这里 <nginx_ws_config>` 有一个Nginx配置WebSocket的例子。

           PyWebIO uses the WebSocket protocol to communicate with the browser in Tornado. If your Tornado application is behind a reverse proxy (such as Nginx), you may need to configure the reverse proxy to support the WebSocket protocol. :ref:`Here <nginx_ws_config>` is an example of Nginx WebSocket configuration.

   .. tab:: Flask

        需要添加两个PyWebIO相关的路由：一个用来提供前端静态文件，另一个用来和浏览器进行Http通讯

        Need to add two routes: one is used to host frontend static files, and the other is used to communicate with the browser through Http::

            from pywebio.platform.flask import webio_view
            from pywebio import STATIC_PATH
            from flask import Flask, send_from_directory

            app = Flask(__name__)

            # `task_func` is PyWebIO task function
            app.add_url_rule('/io', 'webio_view', webio_view(task_func),
                        methods=['GET', 'POST', 'OPTIONS'])  # need GET,POST and OPTIONS methods

            @app.route('/')
            @app.route('/<path:static_file>')
            def serve_static_file(static_file='index.html'):
                """host frontend static files"""
                return send_from_directory(STATIC_PATH, static_file)

            app.run(host='localhost', port=80)

        以上代码使用 `webio_view(task_func) <pywebio.platform.flask.webio_view>` 来获得运行PyWebIO应用的Flask视图 ，
        并调用 `Flask.add_url_rule <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.add_url_rule>`_ 将其绑定在 ``/io`` 路径下；同时编写视图函数 ``serve_static_file`` 将PyWebIO使用的静态文件托管到 ``/`` 路径下。
        启动Flask应用后，访问 ``http://localhost/`` 即可打开PyWebIO应用

        In above code, we use `webio_view(task_func) <pywebio.platform.flask.webio_view>` to get the Flask view of the PyWebIO application, and use `Flask.add_url_rule <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.add_url_rule>`_ to bind it to ``/io`` path. The view function ``serve_static_file`` is used to host the static files used by PyWebIO and is bind to ``/`` path. After starting the Flask application, visit ``http://localhost/`` to open the PyWebIO application.

   .. tab:: Django

        在django的路由配置文件 ``urls.py`` 中加入PyWebIO相关的路由即可

        Need to add two routes in ``urls.py``::

            # urls.py

            from functools import partial
            from django.urls import path
            from django.views.static import serve
            from pywebio import STATIC_PATH
            from pywebio.platform.django import webio_view

            # `task_func` is PyWebIO task function
            webio_view_func = webio_view(task_func)

            urlpatterns = [
                path(r"io", webio_view_func),  # backend API
                path(r'', partial(serve, path='index.html'), {'document_root': STATIC_PATH}),  # host index.html file
                path(r'<path:path>', serve, {'document_root': STATIC_PATH}),  # host other static files
            ]

        需要添加3条路由规则，第一条路由规则将PyWebIO应用的视图函数绑定到 ``/io`` 路径下，第二条路由用于提供PyWebIO的前端index.html文件，最后一个路由用于提供PyWebIO的其他静态文件

        Three routing rules need to be added. The first routing rule binds the view function of the PyWebIO application to the ``/io`` path, the second route is used to host the frontend ``index.html`` file of PyWebIO, and the last route is used to host other PyWebIO static files.

        启动Django应用后，访问 ``http://localhost/`` 即可打开PyWebIO应用

        After starting the Django server, visit ``http://localhost/`` to open the PyWebIO application

   .. tab:: aiohttp

      添加两个PyWebIO相关的路由：一个用来提供前端静态文件，另一个用来和浏览器进行WebSocket通讯

      Need to add two routes: one is used to host frontend static files, and the other is used to communicate with the browser through WebSocket:::

            from aiohttp import web
            from pywebio.platform.aiohttp import static_routes, webio_handler

            app = web.Application()
            # `task_func` is PyWebIO task function
            app.add_routes([web.get('/io', webio_handler(task_func))])  # backend API
            app.add_routes(static_routes('/'))  # host static files

            web.run_app(app, host='localhost', port=80)

      启动aiohttp应用后，访问 ``http://localhost/`` 即可打开PyWebIO应用

      After starting the aiohttp server, visit ``http://localhost/`` to open the PyWebIO application

      .. attention::

        当使用aiohttp后端时，PyWebIO使用WebSocket协议和浏览器进行通讯，如果你的aiohttp应用处在反向代理(比如Nginx)之后，
        可能需要特别配置反向代理来支持WebSocket协议，:ref:`这里 <nginx_ws_config>` 有一个Nginx配置WebSocket的例子。

        PyWebIO uses the WebSocket protocol to communicate with the browser in aiohttp. If your aiohttp server is behind a reverse proxy (such as Nginx), you may need to configure the reverse proxy to support the WebSocket protocol. :ref:`Here <nginx_ws_config>` is an example of Nginx WebSocket configuration.

.. _integration_web_framework_note:

Notes
^^^^^^^^^^^
**Static resources Hosting**

在开发阶段，使用后端框架提供的静态文件服务对于开发和调试都十分方便，上文的与Web框架集成的示例代码也都是使用了后端框架提供的静态文件服务。
但出于性能考虑，托管静态文件最好的方式是使用 `反向代理 <https://en.wikipedia.org/wiki/Reverse_proxy>`_ (比如 `nginx <https://nginx.org/>`_ )
或者 `CDN <https://en.wikipedia.org/wiki/Content_delivery_network>`_ 服务。

Using the web framework to serve static files is very convenient for development and debugging (Just like the above code). But for performance reasons, the best way to host static files is to use a `reverse proxy <https://en.wikipedia.org/wiki/Reverse_proxy>`_ (such as `nginx <https://nginx.org/>`_) or `CDN <https://en.wikipedia.org/wiki/Content_delivery_network>`_ service.

**前端页面和后端接口的路径约定 Path conventions for frontend pages and backend interfaces**

PyWebIO默认通过当前页面的同级的 ``./io`` API与后端进行通讯。

By default, PyWebIO uses ``./io`` API of the current page to communicates with the backend.

例如你将PyWebIO静态文件托管到 ``/A/B/C/(.*)`` 路径下，那么你需要将PyWebIO API的路由绑定到 ``/A/B/C/io`` 处；
你也可以在PyWebIO应用的地址中添加 ``pywebio_api`` url参数来指定PyWebIO后端API地址，
例如 ``/A/B/C/?pywebio_api=/D/pywebio`` 将PyWebIO后端API地址设置到了 ``/D/pywebio`` 处。

For example, if you host PyWebIO static files under the path ``/A/B/C/(.*)``, then you need to bind the route of the PyWebIO backend API to ``/A/B/C/io``. You can also use the ``pywebio_api`` url parameter in page to specify the PyWebIO backend API address, for example, ``/A/B/C/?pywebio_api=/D/pywebio`` sets the PyWebIO backend API address to ``/D/pywebio``.

``pywebio_api`` 参数可以使用相对地址、绝对地址，也可以指定其他服务器。

The ``pywebio_api`` parameter can use a relative address, absolute address or other host.

.. caution::

   需要注意 ``pywebio_api`` 参数的格式：

   Pay attention to the format of the ``pywebio_api`` url parameter:

   * 相对地址可以为 ``./xxx/xxx`` 或 ``xxx/xxx`` 的相对地址格式。
     The relative address can be in the format of ``./xxx/xxx`` or ``xxx/xxx``.
   * 绝对地址以 ``/`` 开头，比如 ``/aaa/bbb`` .
     The absolute address starts with ``/``, such as ``/aaa/bbb``.
   * 指定其他服务器需要使用完整格式: ``http://example.com:5000/aaa/io`` 、 ``ws://example.com:8080/bbb/ws_io`` ,或者省略协议字段: ``//example.com:8080/aaa/io`` 。省略协议字段时，PyWebIO根据当前页面的协议确定要使用的协议: 若当前页面为http协议，则后端接口自动选择http或ws协议；若当前页面为https协议，则后端接口自动选择https或wss协议。
     Specifying other host needs to use the full format, such as ``http://example.com:5000/aaa/io``, ``ws://example.com:8080/bbb/ws_io``, or omit the protocol field: ``//example.com:8080/aaa/io``.
     When the protocol field is omitted, PyWebIO determines the protocol to be used according to the protocol of the current page: if the current page is the http protocol, the protocol of backend API automatically will be http or ws; if the current page is the https protocol, the protocol of backend API automatically will be https or wss.

如果你不想自己托管静态文件，你可以使用PyWebIO的Github Page页面: ``https://wang0618.github.io/PyWebIO/pywebio/html/?pywebio_api=`` ，需要在页面上通过 ``pywebio_api`` 参数传入后端API地址，并且将 ``https://wang0618.github.io`` 加入 ``allowed_origins`` 列表中（见下文"跨域配置"说明）。

If you don’t want to host static files by yourself, you can use PyWebIO's Github Page: ``https://wang0618.github.io/PyWebIO/pywebio/html/?pywebio_api=``, you need to pass in the backend API address to the ``pywebio_api`` parameter , And add ``https://wang0618.github.io`` to the ``allowed_origins`` list (see "CORS setting" section below).

**CORS setting**

当后端API与前端页面不在同一host下时，需要在 `webio_handler() <pywebio.platform.tornado.webio_handler>` 或
`webio_view() <pywebio.platform.flask.webio_view>` 中使用 ``allowed_origins`` 或 ``check_origin``
参数来使后端接口允许前端页面的请求。

When the backend API and the frontend page are not in the same host, you need to use the ``allowed_origins`` or ``check_origin`` parameter in ``webio_handler()`` or ``webio_view()`` to make backend API allow the requests from the frontend page.

.. _coroutine_based_session:

Coroutine-based session
-------------------------------
此部分内容属于高级特性，您不必使用此部分也可以实现PyWebIO支持的全部功能。PyWebIO中所有仅用于协程会话的函数或方法都在文档中有特别说明。

This section will introduce the advanced features of PyWebIO. In most cases, you don’t need it. All functions or methods in PyWebIO that are only used for coroutine sessions are specifically noted in the document.

PyWebIO的会话实现默认是基于线程的，用户每打开一个和服务端的会话连接，PyWebIO会启动一个线程来运行任务函数。
除了基于线程的会话，PyWebIO还提供了基于协程的会话。基于协程的会话接受协程函数作为任务函数。

PyWebIO's session is based on thread by default. Each time a user opens a session connection with the server, PyWebIO will start a thread to run task functions. In addition to thread-based sessions, PyWebIO also provides coroutine-based sessions. Coroutine-based sessions accept coroutine functions as task functions.

基于协程的会话为单线程模型，所有会话都运行在一个线程内。对于IO密集型的任务，协程比线程占用更少的资源同时又拥有媲美于线程的性能。
另外，协程的上下文切换具有可预测性，能够减少程序同步与加锁的需要，可以有效避免大多数临界区问题。

The session based on the coroutine uses a single-threaded model, which means that all sessions run in a single thread. For IO-bound tasks, coroutines take up fewer resources than threads and have performance comparable to threads. In addition, the context switching of the coroutine is predictable, which can reduce the need for program synchronization and locking, and can effectively avoid most critical section problems.

Using coroutine session
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

要使用基于协程的会话，需要使用 ``async`` 关键字将任务函数声明为协程函数，并使用 ``await`` 语法调用PyWebIO输入函数:

To use coroutine-based session, you need to use the ``async`` keyword to declare the task function as a coroutine function, and use the ``await`` syntax to call the PyWebIO input function:

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

In the coroutine task function, you can also use ``await`` to call other coroutines or ( `awaitable objects <https://docs.python.org/3/library/asyncio-task.html#asyncio-awaitables>`_ ) in the standard library `asyncio <https://docs.python.org/3/library/asyncio.html>`_:

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

   In coroutine-based session, all input functions defined in the :doc:`pywebio.input </input>` module need to use ``await`` syntax to get the return value. Forgetting to use ``await`` will be a common error when using coroutine-based session.

   其他在协程会话中也需要使用 ``await`` 语法来进行调用函数有:

   Other functions that need to use ``await`` syntax in the coroutine session are:

    * `pywebio.session.run_asyncio_coroutine(coro_obj) <pywebio.session.run_asyncio_coroutine>`
    * `pywebio.session.eval_js(expression) <pywebio.session.eval_js>`
    * `pywebio.session.hold() <pywebio.session.hold>`

.. warning::

   虽然PyWebIO的协程会话兼容标准库 ``asyncio`` 中的 ``awaitable objects`` ，但 ``asyncio`` 库不兼容PyWebIO协程会话中的 ``awaitable objects`` .

   Although the PyWebIO coroutine session is compatible with the ``awaitable objects`` in the standard library ``asyncio``, the ``asyncio`` library is not compatible with the ``awaitable objects`` in the PyWebIO coroutine session.

   也就是说，无法将PyWebIO中的 ``awaitable objects`` 传入 ``asyncio`` 中的接受 ``awaitable objects`` 作为参数的函数中，比如如下调用是 **不被支持的**

   That is to say, you can't pass PyWebIO ``awaitable objects`` to the `asyncio`` function that accepts ``awaitable objects``. For example, the following calls are **unsupported** ::

      await asyncio.shield(pywebio.input())
      await asyncio.gather(asyncio.sleep(1), pywebio.session.eval_js('1+1'))
      task = asyncio.create_task(pywebio.input())

.. _coroutine_based_concurrency:

Concurrency in coroutine-based sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在基于协程的会话中，你可以启动线程，但是无法在其中调用PyWebIO交互函数（ `register_thread() <pywebio.session.register_thread>` 在协程会话中不可用）。
但你可以使用 `run_async(coro) <pywebio.session.run_async>` 来异步执行一个协程对象，新协程内可以使用PyWebIO交互函数

In coroutine-based session, you can start new thread, but you cannot call PyWebIO interactive functions in it (`register_thread() <pywebio.session.register_thread>` is not available in coroutine session). But you can use `run_async(coro) <pywebio.session.run_async>` to execute a coroutine object asynchronously, and PyWebIO interactive functions can be used in the new coroutine::

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

`run_async(coro) <pywebio.session.run_async>` returns a `TaskHandle <pywebio.session.coroutinebased.TaskHandle>`, which can be used to query the running status of the coroutine or close the coroutine.

Close of session
^^^^^^^^^^^^^^^^^^^
与基于线程的会话类似，在基于协程的会话中，当任务函数和在会话内通过 `run_async() <pywebio.session.run_async>` 运行的协程全部结束后，会话关闭。

Similar to thread-based session, in coroutine-based session, when the task function and the coroutine running through `run_async() <pywebio.session.run_async>` in the session are all finished, the session is closed.

对于因为用户的关闭浏览器而造成的会话结束，处理逻辑和 :ref:`基于线程的会话 <session_close>` 一致:
此时当前会话内还未返回的PyWebIO输入函数调用将抛出 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常，之后对于PyWebIO交互函数的调用将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` 或 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常。

If the close of the session is caused by the user closing the browser, the behavior of PyWebIO is the same as :ref:`Thread-based session <session_close>`: After the browser page closed, PyWebIO input function calls that have not yet returned in the current session will cause `SessionClosedException <pywebio.exceptions.SessionClosedException>`, and subsequent calls to PyWebIO interactive functions will cause `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` or `SessionClosedException <pywebio.exceptions.SessionClosedException>`.

协程会话也同样支持使用 `defer_call(func) <pywebio.session.defer_call>` 来设置会话结束时需要调用的函数。

`defer_call(func) <pywebio.session.defer_call>` also available in coroutine session.

Integration with Web Framework
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

基于协程的会话同样可以与Web框架进行集成，只需要在原来传入任务函数的地方改为传入协程函数即可。

The coroutine-based session can also be integrated with the web framework.

但当前在使用基于协程的会话集成进Flask或Django时，存在一些限制：

However, there are some limitations when using coroutine-based sessions to integrate into Flask or Django:

一是协程函数内还无法直接通过 ``await`` 直接等待asyncio库中的协程对象，目前需要使用 `run_asyncio_coroutine() <pywebio.session.run_asyncio_coroutine>` 进行包装。

First, when ``await`` the coroutine object in the ``asyncio`` module, you need use `run_asyncio_coroutine() <pywebio.session.run_asyncio_coroutine>` to wrap the coroutine object.

二是，在启动Flask/Django这类基于线程的服务器之前需要启动一个单独的线程来运行事件循环。

Secondly, you need to start a new thread to run the event loop before starting a Flask/Django server.

使用基于协程的会话集成进Flask的示例:

Example of coroutine-based session integration into Flask:

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
        await run_asyncio_coroutine(asyncio.sleep(1))  # can't just "await asyncio.sleep(1)"
        put_text('... World!')

    app = Flask(__name__)
    app.add_url_rule('/io', 'webio_view', webio_view(hello_word),
                                methods=['GET', 'POST', 'OPTIONS'])

    @app.route('/')
    @app.route('/<path:static_file>')
    def serve_static_file(static_file='index.html'):
        return send_from_directory(STATIC_PATH, static_file)

    # thread to run event loop
    threading.Thread(target=run_event_loop, daemon=True).start()
    app.run(host='localhost', port=80)

最后，使用PyWebIO编写的协程函数不支持Script模式，总是需要使用 ``start_server`` 来启动一个服务或者集成进Web框架来调用。

Finally, coroutine-based session is not available in the Script mode.

Last but not least
---------------------

以上就是PyWebIO的全部功能了，你可以继续阅读接下来的文档，或者立即开始PyWebIO应用的编写了。

This is all features of PyWebIO, you can continue to read the rest of the documents, or start writing your PyWebIO applications now.

最后再提供一条建议，当你在使用PyWebIO遇到设计上的问题时，可以问一下自己：如果在是在终端程序中我会怎么做？
如果你已经有答案了，那么在PyWebIO中一样可以使用这样的方式完成。如果问题依然存在或者觉得解决方案不够好，
你可以考虑使用 `put_buttons() <pywebio.output.put_buttons>` 提供的回调机制。

Finally, please allow me to provide one more suggestion. When you encounter design problems when using PyWebIO, you can ask yourself a question: What would I do if it is in a terminal program?
If you already have the answer, it can be done in the same way with PyWebIO. If the problem persists or the solution is not good enough, you can consider using the callback mechanism provided by `put_buttons() <pywebio.output.put_buttons>`.

OK, Have fun with PyWebIO!