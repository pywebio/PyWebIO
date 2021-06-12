User's guide
============

If you are familiar with web development, you may not be accustomed to the usage of PyWebIO described below, which is different from the traditional web development patton that backend implement api and frontend display content. In PyWebIO, you only need write code in Python.

In fact, the way of writing PyWebIO applications is more like writing a console program, except that the terminal here becomes a browser. Using the imperative API provided by PyWebIO,
you can simply call ``put_text``, ``put_image``, ``put_table`` and other functions to output text, pictures, tables and other content to the browser, or you can call some functions such as ``input``, ``select``, ``file_upload`` to display different forms on the browser to get user input. In addition, PyWebIO also provides support for click events, layout, etc. PyWebIO aims to allow you to use the least code to interact with the user and provide a good user experience as much as possible.

This user guide introduces you the most of the features of PyWebIO. There is a demo link at the top right of the most of the example codes in this document, where you can preview the running effect of the code online.

Input
------------

The input functions are defined in the :doc:`pywebio.input </input>` module and can be imported using ``from pywebio.input import *``.

When calling the input function, an input form  will be popped up on the browser. PyWebIO's input functions is blocking (same as Python's built-in ``input()`` function) and will not return until the form is successfully submitted.

Basic input
^^^^^^^^^^^^^

Here are some basic types of input.

Text input:

.. exportable-codeblock::
    :name: text-input
    :summary: Text input

    age = input("How old are you?", type=NUMBER)
    put_text('age = %r' % age)  # ..demo-only

After running the above code, the browser will pop up a text input field to get the input. After the user completes the input and submits the form, the function returns the value entered by the user.

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

There are many parameters that can be passed to the input function(for complete parameters, please refer to the :doc:`function document </input>`):

.. exportable-codeblock::
    :name: input-args
    :summary: Parameter of input functions

    input('This is label', type=TEXT, placeholder='This is placeholder',
            help_text='This is help text', required=True)

The results of the above example are as follows:

.. image:: /assets/input_1.png

You can specify a validation function for the input by using ``validate`` parameter. The validation function should return ``None`` when the check passes, otherwise an error message will be returned:

.. exportable-codeblock::
    :name: input-valid-func
    :summary: Input validate function for

    def check_age(p):  # return None when the check passes, otherwise return the error message
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = input("How old are you?", type=NUMBER, validate=check_age)
    put_text('age = %r' % age)  # ..demo-only

When the user input an illegal value, the input field is displayed as follows:

.. image:: /assets/input_2.png

You can use ``code`` parameter in :func:`pywebio.input.textarea()` to make a code editing textarea. This feature uses `Codemirror <https://codemirror.net/>`_ as underlying implementation. The ``code`` parameter accept the Codemirror options as a dict.

.. exportable-codeblock::
    :name: codemirror
    :summary: Code editing by using textarea

    code = textarea('Code Edit', code={
        'mode': "python",  # code language
        'theme': 'darcula',  # Codemirror theme. Visit https://codemirror.net/demo/theme.html#cobalt to get more themes
    }, value='import something\n# Write your python code')
    put_code(code, language='python')  # ..demo-only

The results of the above example are as follows:

.. image:: /assets/codemirror_textarea.png

:ref:`Here <codemirror_options>` are some commonly used Codemirror options. For complete Codemirror options, please visit: https://codemirror.net/doc/manual.html#config

Input Group
^^^^^^^^^^^^^

PyWebIO uses input group to get multiple inputs in a single form. `pywebio.input.input_group()` accepts a list of single input function call as parameter, and returns a dictionary with the ``name`` of the single input function as the key and the input data as the value:


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

The input group also supports using ``validate`` parameter to set the validation function, which accepts the entire form data as parameter:

.. exportable-codeblock::
    :name: input-group
    :summary: Input Group

    def check_age(p):  # single input item validation  # ..demo-only
        if p < 10:                  # ..demo-only
            return 'Too young!!'    # ..demo-only
        if p > 60:                  # ..demo-only
            return 'Too old!!'      # ..demo-only
                                    # ..demo-only
    def check_form(data):  # input group validation: return (input name, error msg) when validation fail
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
   PyWebIO determines whether the input function is in `input_group` or is called alone according to whether the ``name`` parameter is passed. So when calling an input function alone, **do not** set the ``name`` parameter; when calling the input function in `input_group`, you **must** provide the ``name`` parameter.

Output
------------

The output functions are all defined in the :doc:`pywebio.output </output>` module and can be imported using ``from pywebio.output import *``.

When output functions is called, the content will be output to the browser in real time. The output functions can be called at any time during the application lifetime.

Basic Output
^^^^^^^^^^^^^^

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


For all output functions provided by PyWebIO, please refer to the :doc:`pywebio.output </output>` module. In addition, PyWebIO also supports data visualization with some third-party libraries, see :doc:`Third-party library ecology </libraries_support>`.


.. note::

    If you use PyWebIO in interactive execution environment of Python shell, IPython or jupyter notebook,
    you need call `show()` method explicitly to show output::

        >>> put_text("Hello world!").show()
        >>> put_table([
        ...     ['A', 'B'],
        ...     [put_markdown(...), put_text('C')]
        ... ]).show()


.. _combine_output:

Combined Output
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The output functions whose name starts with ``put_`` can be combined with some output functions as part of the final output:

You can pass ``put_xxx()`` calls to `put_table() <pywebio.output.put_table>` as cell content:

.. exportable-codeblock::
    :name: putxxx
    :summary: Combination output

    put_table([
        ['Type', 'Content'],
        ['html', put_html('X<sup>2</sup>')],
        ['text', '<hr/>'],  # equal to ['text', put_text('<hr/>')]
        ['buttons', put_buttons(['A', 'B'], onclick=...)],  # ..doc-only
        ['buttons', put_buttons(['A', 'B'], onclick=put_text)],  # ..demo-only
        ['markdown', put_markdown('`Awesome PyWebIO!`')],
        ['file', put_file('hello.text', b'hello world')],
        ['table', put_table([['A', 'B'], ['C', 'D']])]
    ])

The results of the above example are as follows:

.. image:: /assets/put_table.png

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

In addition, you can use `put_widget() <pywebio.output.put_widget>` to make your own output widgets that can accept ``put_xxx()`` calls.

For a full list of functions that accept ``put_xxx()`` calls as content, see :ref:`Output functions list <output_func_list>`

**Placeholder**

When using combination output, if you want to dynamically update the ``put_xxx()`` content after it has been output, you can use the `output() <pywebio.output.output>` function. `output() <pywebio.output.output>` is like a placeholder, it can be passed in anywhere that ``put_xxx()`` can passed in. And after being output, the content can also be modified:

.. exportable-codeblock::
    :name: output
    :summary: Output placeholder——`output()`

    hobby = output('Coding')  # equal to output(put_text('Coding'))
    put_table([
        ['Name', 'Hobbies'],
        ['Wang', hobby]      # hobby is initialized to Coding
    ])
    ## ----

    hobby.reset('Movie')  # hobby is reset to Movie
    ## ----
    hobby.append('Music', put_text('Drama'))   # append Music, Drama to hobby
    ## ----
    hobby.insert(0, put_markdown('**Coding**'))  # insert the Coding into the top of the hobby

**Context Manager**

Some output functions that accept ``put_xxx()`` calls as content can be used as context manager:

.. exportable-codeblock::
    :name: output-context-manager
    :summary: Output as context manager

    with put_collapse('This is title'):
        for i in range(4):
            put_text(i)

        put_table([
            ['Commodity', 'Price'],
            ['Apple', '5.5'],
            ['Banana', '7'],
        ])

For a full list of functions that support context manager, see :ref:`Output functions list <output_func_list>`

Callback
^^^^^^^^^^^^^^

As we can see from the above, the interaction of PyWebIO has two parts: input and output. The input function of PyWebIO is blocking, a form will be displayed on the user's web browser when calling input function, the input function will not return until the user submits the form. The output function is used to output content to the browser in real time. The input/output behavior of PyWebIO is consistent with the console program. That's why we say PyWebIO turning the browser into a "rich text terminal". So you can write PyWebIO applications in script programing way.

In addition, PyWebIO also supports event callbacks: PyWebIO allows you to output some buttons and bind callbacks to them. The provided callback function will be executed when the button is clicked.

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

The call to `put_table() <pywebio.output.put_table>` will not block. When user clicks a button, the corresponding callback function will be invoked:

.. image:: /assets/table_onclick.*

Of course, PyWebIO also supports outputting individual button:

.. exportable-codeblock::
    :name: put-buttons
    :summary: Event callback of button widget

    def btn_click(btn_val):
        put_text("You click %s button" % btn_val)
    put_buttons(['A', 'B', 'C'], onclick=btn_click)

.. note::
   After the PyWebIO session (see :ref:`Server and script mode <server_and_script_mode>` for more information about session) closed, the event callback will not work. You can call the :func:`pywebio.session.hold()` function at the end of the task function to hold the session, so that the event callback will always be available before the browser page is closed by user.

Output Scope
^^^^^^^^^^^^^^

PyWebIO uses the scope model to give more control to the location of content output. The output area of PyWebIO can be divided into different output domains. The output domain is called Scope in PyWebIO.

The output domain is a container of output content, and each output domain is arranged vertically, and the output domains can also be nested.

Each output function (function name like ``put_xxx()``) will output its content to a scope, the default is "current scope". "current scope" is determined by the runtime context. The output function can also manually specify the scope to output. The scope name is unique within the session.

.. _use_scope:

**use_scope()**

You can use `use_scope() <pywebio.output.use_scope>` to open and enter a new output scope, or enter an existing output scope:

.. exportable-codeblock::
    :name: use-scope
    :summary: use `use_scope()` to open or enter scope

    with use_scope('scope1'):  # open and enter a new output: 'scope1'
        put_text('text1 in scope1')  # output text to scope1

    put_text('text in parent scope of scope1')  # output text to ROOT scope

    with use_scope('scope1'):  # enter an existing scope: 'scope1'
        put_text('text2 in scope1')  # output text to scope1

The results of the above code are as follows::

    text1 in scope1
    text2 in scope1
    text in parent scope of scope1

You can use ``clear`` parameter in `use_scope() <pywebio.output.use_scope>` to clear the previous content in the scope:

.. exportable-codeblock::
    :name: use-scope
    :summary: `use_scope()`'s `clear` parameter

    with use_scope('scope2'):
        put_text('create scope2')

    put_text('text in parent scope of scope2')
    ## ----

    with use_scope('scope2', clear=True):  # enter the existing scope and clear the previous content
        put_text('text in scope2')

The results of the above code are as follows::

    text in scope2
    text in parent scope of scope2

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

When calling ``show_time()`` for the first time, a ``time`` scope will be created, and the current time will be output to it. And then every time the ``show_time()`` is called, the new content will replace the previous content.

Scopes can be nested. At the beginning, PyWebIO applications have only one ``ROOT`` Scope. Each time a new scope is created, the nesting level of the scope will increase by one level, and each time the current scope is exited, the nesting level of the scope will be reduced by one. PyWebIO uses the Scope stack to save the scope nesting level at runtime.

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


The above code will generate the following scope layout::

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

The output function (function name like ``put_xxx()``) will output the content to the "current scope" by default, and the "current scope" of the runtime context can be set by ``use_scope()``.

In addition, you can use the ``scope`` parameter of the output function to specify the destination scope to output:

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

In addition to directly specifying the target scope name, the ``scope`` parameter can also accept an integer to determine the scope by indexing the scope stack: 0 means the top level scope(the ROOT Scope), -1 means the current scope, -2 means the scope used before entering the current scope, ...

By default, the content output to the same scope will be arranged from top to bottom according to the calling order of the output function. The output content can be inserted into other positions of the target scope by using the ``position`` parameter of the output function.

Each output item in a scope has an index, the first item's index is 0, and the next item's index is incremented by one. You can also use a negative number to index the items in the scope, -1 means the last item, -2 means the item before the last...

The ``position`` parameter of output functions accepts an integer. When ``position>=0``, it means to insert content before the item whose index equal ``position``; when ``position<0``, it means to insert content after the item whose index equal ``position``:

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

When performing some continuous output (such as log output), you may want to scroll the page to the bottom automatically when there is new output. You can call `set_env(auto_scroll_bottom=True) <pywebio.session.set_env>` to enable automatic scrolling. Note that when enabled, only outputting to ROOT scope can trigger automatic scrolling.

**Output Animation**

By default, PyWebIO will use the fade-in animation effect to display the content. You can use `set_env(output_animation=False) <pywebio.session.set_env>` to turn off the animation.

To view the effects of environment settings, please visit :demo_host:`set_env Demo </set_env_demo>`

Layout
^^^^^^^^^^^^^^

In general, using the output functions introduced above is enough to output what you want, but these outputs are arranged vertically. If you want to create a more complex layout (such as displaying a code block on the left side of the page and an image on the right), you need to use layout functions.

The ``pywebio.output`` module provides 3 layout functions, and you can create complex layouts by combining them:

* `put_row() <pywebio.output.put_row>` : Use row layout to output content. The content is arranged horizontally
* `put_column() <pywebio.output.put_column>` : Use column layout to output content. The content is arranged vertically
* `put_grid() <pywebio.output.put_grid>` : Output content using grid layout

Here is an example by combining ``put_row()`` and ``put_column()``:

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

The results of the above example are as follows:

.. image:: /assets/layout.png
   :align: center

The layout function also supports customizing the size of each part::

    put_row([put_image(...), put_image(...)], size='40% 60%')  # The ratio of the width of two images is 2:3

For more information, please refer to the :ref:`layout functions documentation <style_and_layout>`.

.. _style:

Style
^^^^^^^^^^^^^^

If you are familiar with `CSS <https://en.wikipedia.org/wiki/CSS>`_ styles,
you can use the ``style()`` method of output return to set a custom style for the output.

You can set the CSS style for a single ``put_xxx()`` output:

.. exportable-codeblock::
    :name: style
    :summary: style of output

    put_text('hello').style('color: red; font-size: 20px')

    ## ----
    put_row([
        put_text('hello').style('color: red'),
        put_markdown('markdown')
    ]).style('margin-top: 20px')


.. _server_and_script_mode:

Server mode and Script mode
------------------------------------

In PyWebIO, there are two modes to run PyWebIO applications: running as a script and using `start_server() <pywebio.platform.tornado.start_server>` or `path_deploy() <pywebio.platform.path_deploy>` to run as a web service.

Overview
^^^^^^^^^^^^^^

.. _server_mode:

**Server mode**

In server mode, PyWebIO will start a web server to continuously provide services. When the user accesses the service address, PyWebIO will open a new session and run PyWebIO application in it.

Use `start_server() <pywebio.platform.tornado.start_server>` to start a web server and serve given PyWebIO applications on it. `start_server() <pywebio.platform.tornado.start_server>` accepts a function as PyWebIO application. In addition, `start_server() <pywebio.platform.tornado.start_server>` also accepts a list of task function or a dictionary of it, so  one PyWebIO Server can have multiple services with different functions. You can use `go_app() <pywebio.session.go_app>` or `put_link() <pywebio.output.put_link>` to jump between services::

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

    # equal to `start_server({'index': index, 'task_1': task_1, 'task_2': task_2})`
    start_server([index, task_1, task_2])


The `start_server() <pywebio.platform.tornado.start_server>` provide a remote access support, when enabled (by passing `remote_access=True` to `start_server()`), you can get a temporary public network access address for the current application, others can access your application via this address. Using remote access makes it easy to temporarily share the application with others. This service is powered by `localhost.run <https://localhost.run>`_.

Use `path_deploy() <pywebio.platform.path_deploy>` to deploy the PyWebIO applications from a directory.
The python file under this directory need contain the ``main`` function to be seen as the PyWebIO application.
You can access the application by using the file path as the URL.

For example, given the following folder structure::

   .
   ├── A
   │   └── a.py
   ├── B
   │   └── b.py
   └── c.py

If you use this directory in `path_deploy() <pywebio.platform.path_deploy>`, you can access the PyWebIO application in ``b.py`` by using URL ``http://<host>:<port>/A/b``.
And if the files have been modified after run `path_deploy() <pywebio.platform.path_deploy>`, you can use ``reload`` URL parameter to reload application in the file: ``http://<host>:<port>/A/b?reload``

You can also use the command ``pywebio-path-deploy`` to start a server just like using `path_deploy() <pywebio.platform.path_deploy>`. For more information, refer ``pywebio-path-deploy --help``

In Server mode, you can use `pywebio.platform.seo()` to set the `SEO <https://en.wikipedia.org/wiki/Search_engine_optimization>`_ information. If ``seo()`` is not used, the `docstring <https://www.python.org/dev/peps/pep-0257/>`_ of the task function will be regarded as SEO information by default.

.. attention::

    Note that in Server mode, all functions from ``input``, ``output`` and ``session`` modules can only be called in the context of task functions. For example, the following code is **not allowed**::

        import pywebio
        from pywebio.input import input

        port = input('Input port number:')   # ❌ error
        pywebio.start_server(my_task_func, port=int(port))


**Script mode**

In Script mode, PyWebIO input and output functions can be called anywhere.

If the user closes the browser before the end of the session, then calls to PyWebIO input and output functions in the session will cause a `SessionException <pywebio.exceptions.SessionException>` exception.

.. _thread_in_server_mode:

Concurrent
^^^^^^^^^^^^^^

PyWebIO can be used in a multi-threading environment.

**Script mode**

In Script mode, you can freely start new thread and call PyWebIO interactive functions in it. When all `non-daemonic <https://docs.python.org/3/library/threading.html#thread-objects>`_ threads finish running, the script exits.

**Server mode**

In Server mode, if you need to use PyWebIO interactive functions in new thread, you need to use `register_thread(thread) <pywebio.session.register_thread>` to register the new thread (so that PyWebIO can know which session the thread belongs to). If the PyWebIO interactive function is not used in the new thread, no registration is required. Threads that are not registered with `register_thread(thread) <pywebio.session.register_thread>` calling PyWebIO's interactive functions will cause `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>`. When both the task function of the session and the thread registered through `register_thread(thread) <pywebio.session.register_thread>` in the session have finished running, the session is closed.

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

The close of session may also be caused by the user closing the browser page. After the browser page is closed, PyWebIO input function calls that have not yet returned in the current session will cause `SessionClosedException <pywebio.exceptions.SessionClosedException>`, and subsequent calls to PyWebIO interactive functions will cause `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` or `SessionClosedException <pywebio.exceptions.SessionClosedException>`.

You can use `defer_call(func) <pywebio.session.defer_call>` to set the function to be called when the session closes. Whether it is because the user closes the page or the task finishes to cause session closed, the function set by `defer_call(func) <pywebio.session.defer_call>` will be executed. `defer_call(func) <pywebio.session.defer_call>` can be used for resource cleaning. You can call `defer_call(func) <pywebio.session.defer_call>` multiple times in the session, and the set functions will be executed sequentially after the session closes.

.. _integration_web_framework:

Integration with web framework
---------------------------------

The PyWebIO application can be integrated into an existing Python Web project, the PyWebIO application and the Web project share a web framework. PyWebIO currently supports integration with Flask, Tornado, Django, aiohttp and FastAPI(Starlette) web frameworks.

The integration methods of those web frameworks are as follows:

.. tabs::

   .. tab:: Tornado

        .. only:: latex

            **Tornado**

        Use `pywebio.platform.tornado.webio_handler()` to get the `WebSocketHandler <https://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketHandler>`_ class for running PyWebIO applications in Tornado::

            import tornado.ioloop
            import tornado.web
            from pywebio.platform.tornado import webio_handler

            class MainHandler(tornado.web.RequestHandler):
                def get(self):
                    self.write("Hello, world")

            if __name__ == "__main__":
                application = tornado.web.Application([
                    (r"/", MainHandler),
                    (r"/tool", webio_handler(task_func)),  # `task_func` is PyWebIO task function
                ])
                application.listen(port=80, address='localhost')
                tornado.ioloop.IOLoop.current().start()


        In above code, we add a routing rule to bind the ``WebSocketHandler`` of the PyWebIO application to the ``/tool`` path.
        After starting the Tornado server, you can visit ``http://localhost/tool`` to open the PyWebIO application.

        .. attention::

           PyWebIO uses the WebSocket protocol to communicate with the browser in Tornado. If your Tornado application is behind a reverse proxy (such as Nginx), you may need to configure the reverse proxy to support the WebSocket protocol. :ref:`Here <nginx_ws_config>` is an example of Nginx WebSocket configuration.

   .. tab:: Flask

        .. only:: latex

            **Flask**

        Use `pywebio.platform.flask.webio_view()` to get the view function for running PyWebIO applications in Flask::

            from pywebio.platform.flask import webio_view
            from flask import Flask

            app = Flask(__name__)

            # `task_func` is PyWebIO task function
            app.add_url_rule('/tool', 'webio_view', webio_view(task_func),
                        methods=['GET', 'POST', 'OPTIONS'])  # need GET,POST and OPTIONS methods

            app.run(host='localhost', port=80)


        In above code, we add a routing rule to bind the view function of the PyWebIO application to the ``/tool`` path.
        After starting the Flask application, visit ``http://localhost/tool`` to open the PyWebIO application.

   .. tab:: Django

        .. only:: latex

            **Django**

        Use `pywebio.platform.django.webio_view()` to get the view function for running PyWebIO applications in Django::

            # urls.py

            from django.urls import path
            from pywebio.platform.django import webio_view

            # `task_func` is PyWebIO task function
            webio_view_func = webio_view(task_func)

            urlpatterns = [
                path(r"tool", webio_view_func),
            ]


        In above code, we add a routing rule to bind the view function of the PyWebIO application to the ``/tool`` path.
        After starting the Django server, visit ``http://localhost/tool`` to open the PyWebIO application

   .. tab:: aiohttp

      .. only:: latex

         **aiohttp**

      Use `pywebio.platform.aiohttp.webio_handler()` to get the `Request Handler <https://docs.aiohttp.org/en/stable/web_quickstart.html#aiohttp-web-handler>`_ coroutine for running PyWebIO applications in aiohttp::

            from aiohttp import web
            from pywebio.platform.aiohttp import webio_handler

            app = web.Application()
            # `task_func` is PyWebIO task function
            app.add_routes([web.get('/tool', webio_handler(task_func))])

            web.run_app(app, host='localhost', port=80)

      After starting the aiohttp server, visit ``http://localhost/tool`` to open the PyWebIO application

      .. attention::

        PyWebIO uses the WebSocket protocol to communicate with the browser in aiohttp. If your aiohttp server is behind a reverse proxy (such as Nginx), you may need to configure the reverse proxy to support the WebSocket protocol. :ref:`Here <nginx_ws_config>` is an example of Nginx WebSocket configuration.


   .. tab:: FastAPI/Starlette

      .. only:: latex

         **FastAPI/Starlette**

      Use `pywebio.platform.fastapi.webio_routes()` to get the FastAPI/Starlette routes for running PyWebIO applications.
      You can mount the routes to your FastAPI/Starlette app.

      FastAPI::

         from fastapi import FastAPI
         from pywebio.platform.fastapi import webio_routes

         app = FastAPI()

         @app.get("/app")
         def read_main():
            return {"message": "Hello World from main app"}

         # `task_func` is PyWebIO task function
         app.mount("/tool", FastAPI(routes=webio_routes(task_func)))

      Starlette::

         from starlette.applications import Starlette
         from starlette.responses import JSONResponse
         from starlette.routing import Route, Mount
         from pywebio.platform.fastapi import webio_routes

         async def homepage(request):
            return JSONResponse({'hello': 'world'})

         app = Starlette(routes=[
            Route('/', homepage),
            Mount('/tool', routes=webio_routes(task_func))  # `task_func` is PyWebIO task function
         ])

      After starting the server by using ``uvicorn <module>:app`` , visit ``http://localhost:8000/tool/`` to open the PyWebIO application

      See also: `FastAPI doc <https://fastapi.tiangolo.com/advanced/sub-applications/>`_ , `Starlette doc <https://www.starlette.io/routing/#submounting-routes>`_

      .. attention::

        PyWebIO uses the WebSocket protocol to communicate with the browser in FastAPI/Starlette. If your server is behind a reverse proxy (such as Nginx), you may need to configure the reverse proxy to support the WebSocket protocol. :ref:`Here <nginx_ws_config>` is an example of Nginx WebSocket configuration.


.. _integration_web_framework_note:

Notes
^^^^^^^^^^^
**Deployment in production**

In your production system, you may want to deploy the web applications with some WSGI/ASGI servers such as uWSGI, Gunicorn, and Uvicorn.
Since PyWebIO applications store session state in memory of process, when you use HTTP-based sessions (Flask and Django) and spawn multiple workers to handle requests,
the request may be dispatched to a process that does not hold the session to which the request belongs.
So you can only start one worker to handle requests when using Flask or Django backend.

If you still want to use multiple processes to increase concurrency, one way is to use Uvicorn+FastAPI, or you can also start multiple Tornado/aiohttp processes and add external load balancer (such as HAProxy or nginx) before them.
Those backends use the WebSocket protocol to communicate with the browser in PyWebIO, so there is no the issue as described above.

**Static resources Hosting**

By default, the front-end of PyWebIO gets required static resources from CDN. If you want to deploy PyWebIO applications in an offline environment, you need to host static files by yourself, and set the ``cdn`` parameter of ``webio_view()`` or ``webio_handler()`` to ``False``.

When setting ``cdn=False`` , you need to host the static resources in the same directory as the PyWebIO application.
In addition, you can also pass a string to ``cdn`` parameter to directly set the URL of PyWebIO static resources directory.

The path of the static file of PyWebIO is stored in ``pywebio.STATIC_PATH``, you can use the command ``python3 -c "import pywebio; print(pywebio.STATIC_PATH)"`` to print it out.

.. note:: ``start_server()`` and ``path_deploy()`` also support ``cdn`` parameter, if it is set to ``False``, the static resource will be hosted in local server automatically, without manual hosting.


.. _coroutine_based_session:

Coroutine-based session
-------------------------------

This section will introduce the advanced features of PyWebIO --- coroutine-based session. In most cases, you don’t need it. All functions or methods in PyWebIO that are only used for coroutine sessions are specifically noted in the document.

PyWebIO's session is based on thread by default. Each time a user opens a session connection to the server, PyWebIO will start a thread to run the task function. In addition to thread-based sessions, PyWebIO also provides coroutine-based sessions. Coroutine-based sessions accept coroutine functions as task functions.

The session based on the coroutine is a single-thread model, which means that all sessions run in a single thread. For IO-bound tasks, coroutines take up fewer resources than threads and have performance comparable to threads. In addition, the context switching of the coroutine is predictable, which can reduce the need for program synchronization and locking, and can effectively avoid most critical section problems.

Using coroutine session
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


In the coroutine task function, you can also use ``await`` to call other coroutines or ( `awaitable objects <https://docs.python.org/3/library/asyncio-task.html#asyncio-awaitables>`_ ) in the standard library `asyncio <https://docs.python.org/3/library/asyncio.html>`_:

.. code-block:: python
   :emphasize-lines: 6,10

    import asyncio
    from pywebio import start_server

    async def hello_word():
        put_text('Hello ...')
        await asyncio.sleep(1)  # await awaitable objects in asyncio
        put_text('... World!')

    async def main():
        await hello_word()  # await coroutine
        put_text('Bye, bye')

    start_server(main, auto_open_webbrowser=True)

.. attention::

   In coroutine-based session, all input functions defined in the :doc:`pywebio.input </input>` module need to use ``await`` syntax to get the return value. Forgetting to use ``await`` will be a common error when using coroutine-based session.

   Other functions that need to use ``await`` syntax in the coroutine session are:

    * `pywebio.session.run_asyncio_coroutine(coro_obj) <pywebio.session.run_asyncio_coroutine>`
    * `pywebio.session.eval_js(expression) <pywebio.session.eval_js>`
    * `pywebio.session.hold() <pywebio.session.hold>`

.. warning::

   Although the PyWebIO coroutine session is compatible with the ``awaitable objects`` in the standard library ``asyncio``, the ``asyncio`` library is not compatible with the ``awaitable objects`` in the PyWebIO coroutine session.

   That is to say, you can't pass PyWebIO ``awaitable objects`` to the ``asyncio`` functions that accept ``awaitable objects``. For example, the following calls are **not supported** ::

      await asyncio.shield(pywebio.input())
      await asyncio.gather(asyncio.sleep(1), pywebio.session.eval_js('1+1'))
      task = asyncio.create_task(pywebio.input())

.. _coroutine_based_concurrency:

Concurrency in coroutine-based sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In coroutine-based session, you can start new thread, but you cannot call PyWebIO interactive functions in it (`register_thread() <pywebio.session.register_thread>` is not available in coroutine session). But you can use `run_async(coro) <pywebio.session.run_async>` to execute a coroutine object asynchronously, and PyWebIO interactive functions can be used in the new coroutine:

.. code-block:: python
   :emphasize-lines: 10

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


`run_async(coro) <pywebio.session.run_async>` returns a `TaskHandler <pywebio.session.coroutinebased.TaskHandler>`, which can be used to query the running status of the coroutine or close the coroutine.

Close of session
^^^^^^^^^^^^^^^^^^^

Similar to thread-based session, in coroutine-based session, when the task function and the coroutine running through `run_async() <pywebio.session.run_async>` in the session are all finished, the session is closed.

If the close of the session is caused by the user closing the browser, the behavior of PyWebIO is the same as :ref:`Thread-based session <session_close>`: After the browser page closed, PyWebIO input function calls that have not yet returned in the current session will cause `SessionClosedException <pywebio.exceptions.SessionClosedException>`, and subsequent calls to PyWebIO interactive functions will cause `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` or `SessionClosedException <pywebio.exceptions.SessionClosedException>`.

`defer_call(func) <pywebio.session.defer_call>` also available in coroutine session.

.. _coroutine_web_integration:

Integration with Web Framework
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The PyWebIO application that using coroutine-based session can also be integrated to the web framework.

However, there are some limitations when using coroutine-based sessions to integrate into Flask or Django:

First, when ``await`` the coroutine objects/awaitable objects in the ``asyncio`` module, you need to use `run_asyncio_coroutine() <pywebio.session.run_asyncio_coroutine>` to wrap the coroutine object.

Secondly, you need to start a new thread to run the event loop before starting a Flask/Django server.

Example of coroutine-based session integration into Flask:

.. code-block:: python
   :emphasize-lines: 12,20

    import asyncio
    import threading
    from flask import Flask, send_from_directory
    from pywebio import STATIC_PATH
    from pywebio.output import *
    from pywebio.platform.flask import webio_view
    from pywebio.platform import run_event_loop
    from pywebio.session import run_asyncio_coroutine

    async def hello_word():
        put_text('Hello ...')
        await run_asyncio_coroutine(asyncio.sleep(1))  # can't just "await asyncio.sleep(1)"
        put_text('... World!')

    app = Flask(__name__)
    app.add_url_rule('/hello', 'webio_view', webio_view(hello_word),
                                methods=['GET', 'POST', 'OPTIONS'])

    # thread to run event loop
    threading.Thread(target=run_event_loop, daemon=True).start()
    app.run(host='localhost', port=80)

Finally, coroutine-based session is not available in the script mode. You always need to use ``start_server()`` to run coroutine task function or integrate it to a web framework.

Last but not least
---------------------

This is all features of PyWebIO, you can continue to read the rest of the documents, or start writing your PyWebIO applications now.

Finally, please allow me to provide one more suggestion. When you encounter a design problem when using PyWebIO, you can ask yourself a question: What would I do if it is in a terminal program?
If you already have the answer, it can be done in the same way with PyWebIO. If the problem persists or the solution is not good enough, you can consider the :doc:`pin <./pin>` module.

OK, Have fun with PyWebIO!