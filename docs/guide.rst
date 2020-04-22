User's guide
============


输入
------------

输入函数都定义在 :doc:`pywebio.input </input>` 模块中，可以使用 ``from pywebio.input import *`` 引入。

基本输入
^^^^^^^^^^^

首先是一些基本类型的输入

文本输入::

    age = input("How old are you?", type=NUMBER)

这样一行代码的效果如下，浏览器会弹出一个文本输入框来获取输入，在表单被提交之前，``input`` 函数不会返回。

一些其他类型的输入::

    # 密码输入
    password = input("Input password", type=PASSWORD)

    # 下拉选择框
    gift = select('Which gift you want?', ['keyboard', 'ipad'])

    # CheckBox
    agree = checkbox("用户协议", options=['I agree to terms and conditions'])

    # Text Area
    text = textarea('Text Area', rows=3, placeholder='Some text')

    # 文件上传
    img = file_upload("Select a image:", accept="image/*")


输入选项
^^^^^^^^^^^

输入函数可指定的参数非常丰富（全部参数及含义请见 :doc:`函数文档 </input>` ）::

    input('This is label', type=TEXT, placeholder='This is placeholder',
            help_text='This is help text', required=True)

则将在浏览器上显示如下：

.. image:: /assets/input_1.png

我们可以为输入指定校验函数，校验函数校验通过时返回None，否则返回错误消息::

    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = input("How old are you?", type=NUMBER, valid_func=check_age)

当用户输入了不合法的值时，页面上的显示如下:

.. image:: /assets/input_2.png


:func:`pywebio.input.textarea` 还支持使用 `Codemirror <https://codemirror.net/>`_ 实现代码风格的编辑区，只需使用 ``code`` 参数传入Codemirror支持的选项即可(最简单的情况是直接传入 ``code={}`` 或 ``code=True``)::

    code = textarea('Code Edit', code={
        'mode': "python",  # 编辑区代码语言
        'theme': 'darcula',  # 编辑区darcula主题, Visit https://codemirror.net/demo/theme.html#cobalt to get more themes
    }, value='import something\n# Write your python code')

文本框的显示效果为：

.. image:: /assets/codemirror_textarea.png

:ref:`这里 <codemirror_options>` 列举了一些常用的Codemirror选项

完整的Codemirror选项请见：https://codemirror.net/doc/manual.html#config

输入组
^^^^^^^

PyWebIO还支持一组输入, 返回结果为一个字典。`pywebio.input.input_group()` 接受单项输入组成的列表作为参数，同时为了在返回的结果中区别出每一项输入，还需要在单项输入函数中传入name参数，input_group返回的字典就是以单项输入函数中的name作为键::

    data = input_group("Basic info",[
      input('Input your name', name='name'),
      input('Input your age', name='age', type=NUMBER, valid_func=check_age)
    ], valid_func=check_form)
    print(data['name'], data['age'])

输入组中同样支持设置校验函数，其接受整个表单数据作为参数::

    def check_form(data):  # 检验函数校验通过时返回None，否则返回 (input name,错误消息)
        if len(data['name']) > 6:
            return ('name', '名字太长！')
        if data['age'] <= 0:
            return ('age', '年龄不能为负数！')

.. note::
   PyWebIO 根据是否在输入函数中传入 ``name`` 参数来判断输入函数是在 `input_group` 中还是被单独调用。
   所以当你想要单独调用一个输入函数时，请不要设置 ``name`` 参数；而在 `input_group` 中调用输入函数时，**务必提供** ``name`` 参数

输出
------------

输出函数都定义在 :doc:`pywebio.output </output>` 模块中，可以使用 ``from pywebio.output import *`` 引入。

基本输出
^^^^^^^^^^^^^^

PyWebIO提供了一些便捷函数来输出表格、链接等格式::

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

所有输出内容的函数名都以 ``put_`` 开始

PyWebIO提供的全部输出函数请见 :doc:`pywebio.output </output>` 模块

事件回调
^^^^^^^^^^^^^^

PyWebIO把程序与用户的交互分成了输入和输出两部分：输入函数为阻塞式调用，在用户提交表单之前将不会返回；对输出函数的调用将会立刻将内容输出至浏览器。
这非常符合控制台程序的编写逻辑。但PyWebIO能做的还远远不止这些，PyWebIO还允许你输出一些控件，当控件被点击时执行提供的回调函数，就像编写GUI程序一样。

下面是一个例子::

    from functools import partial

    def edit_row(choice, row):
        put_text("You click %s button ar row %s" % (choice, row))

    put_table([
        ['Idx', 'Actions'],
        [1, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])

`put_table() <pywebio.output.put_table>` 的调用不会阻塞。当用户点击了某行中的按钮时，PyWebIO会自动调用相应的处理函数:

.. image:: /assets/table_onclick.*

当然，PyWebIO还支持单独的按钮控件::

    def btn_click(btn_val):
        put_text("You click %s button" % btn_val)
    put_buttons(['A', 'B', 'C'], onclick=btn_click)

.. note::
   在PyWebIO会话(关于会话的概念见下文 :ref:`Server and script mode <server_and_script_mode>` )结束后，事件回调也将不起作用，你可以在任务函数末尾处使用 :func:`pywebio.session.hold()` 函数来将会话保持，这样在用户关闭浏览器前，事件回调将一直可用。

锚点
^^^^^^^^^^^^^^
就像在控制台输出文本一样，PyWebIO默认在页面的末尾输出各种内容，你可以使用锚点来改变这一行为。

你可以调用 `set_anchor(name) <pywebio.output.set_anchor>` 对当前输出位置进行标记。

你可以在任何输出函数中使用 ``before`` 参数将内容插入到指定的锚点之前，也可以使用 ``after`` 参数将内容插入到指定的锚点之后。

在输出函数中使用 ``anchor`` 参数为当前的输出内容标记锚点，若锚点已经存在，则将锚点处的内容替换为当前内容。

以下代码展示了在输出函数中使用锚点::

    set_anchor('top')
    put_text('A')
    put_text('B', anchor='b')
    put_text('C', after='top')
    put_text('D', before='b')

以上代码将输出::

    C
    A
    D
    B

PyWebIO还提供了以下锚点控制函数：

* `set_anchor(anchor) <pywebio.output.set_anchor>` 可以清除 ``anchor`` 锚点之前输出的内容
* `clear_after(anchor) <pywebio.output.clear_after>` 可以清除 ``anchor`` 锚点之后输出的内容
* `clear_range(start_anchor, end_anchor) <pywebio.output.clear_range>` 可以清除 ``start_anchor`` 到 ``end_anchor`` 锚点之间的内容
* `scroll_to(anchor) <pywebio.output.scroll_to>`  可以将页面滚动到 ``anchor`` 锚点处


页面环境设置
^^^^^^^^^^^^^^

**输出区外观**

PyWebIO支持两种外观：输出区固定高度/可变高度。
可以通过调用 `set_output_fixed_height(True) <pywebio.output.set_output_fixed_height>` 来开启输出区固定高度。

**设置页面标题**

调用 `set_title(title) <pywebio.output.set_title>` 可以设置页面标题。

**自动滚动**

在不指定锚点进行输出时，PyWebIO默认在输出完毕后自动将页面滚动到页面最下方；在调用输入函数时，也会将页面滚动到表单处。
通过调用 `set_auto_scroll_bottom(False) <pywebio.output.set_auto_scroll_bottom>` 来关闭自动滚动。

.. _server_and_script_mode:

Server mode & Script mode
------------------------------------

在 :ref:`Hello, world <hello_word>` 一节中，已经知道，PyWebIO支持在普通的脚本中调用和使用
`start_server() <pywebio.platform.start_server>` 启动一个Web服务两种模式。

Server mode 下，需要提供一个任务函数来为每个用户提供服务，当用户访问服务地址时，PyWebIO会开启一个新会话并运行任务函数。
在任务函数外不能调用PyWebIO的交互函数，但是在由任务函数调用的其他函数内依然可以调用PyWebIO的交互函数。
在调用 ``start_server()`` 启动Web服务之前，不允许调用任何PyWebIO的交互函数。

比如如下调用是 **不被允许的** ::

    import pywebio
    from pywebio.input import input

    port = input('Input port number:')
    pywebio.start_server(some_func(), port=int(port))


Script mode 下，在任何位置都可以调用PyWebIO的交互函数。

如果用户在会话结束之前关闭了浏览器，那么之后会话内对于PyWebIO交互函数的调用将会引发一个 ``SessionException`` 异常。

并发
^^^^^^^^^^^^^^

PyWebIO 支持在多线程环境中使用。

**Script mode**

在 Script mode 下，你可以自由地启动线程，并在其中调用PyWebIO的交互函数。当所有非 `Daemon线程 <https://docs.python.org/3/library/threading.html#thread-objects>`_ 运行结束后，脚本退出。

**Server mode**

Server mode 下，由于对多会话的支持，如果需要在新创建的线程中使用PyWebIO的交互函数，需要手动调用 `register_thread(thread) <pywebio.session.register_thread>` 对新进程进行注册。
如果新创建的线程中没有使用到PyWebIO的交互函数，则无需注册。在没有使用 `register_thread(thread) <pywebio.session.register_thread>` 注册的线程不受会话管理，其调用PyWebIO的交互函数将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` 异常。
当会话的任务函数和会话内通过 `register_thread(thread) <pywebio.session.register_thread>` 注册的线程都结束运行时，会话关闭。

会话的结束
^^^^^^^^^^^^^^

会话还会因为用户的关闭浏览器而结束，这时当前会话内还未返回的PyWebIO输入函数调用将抛出 `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常，之后对于PyWebIO交互函数的调用将会产生 `SessionNotFoundException <pywebio.exceptions.SessionNotFoundException>` / `SessionClosedException <pywebio.exceptions.SessionClosedException>` 异常。

可以使用 `defer_call(func) <pywebio.session.defer_call>` 来设置会话结束时需要调用的函数。无论是用户主动关闭会话还是任务结束会话关闭，设置的函数都会被执行。
可以用于资源清理等工作。在会话中可以多次调用 `defer_call() <pywebio.session.defer_call>` ,会话结束后将会顺序执行设置的函数。


与Web框架集成
---------------

.. _integration_web_framework:

PyWebIO 目前支持与Flask和Tornado Web框架的集成。
与Web框架集成需要完成两件事情：托管PyWebIO静态文件；暴露PyWebIO后端接口。
这其中需要注意静态文件和后端接口的路径约定，以及静态文件与后端接口分开部署时因为跨域而需要的特别设置。

与Tornado集成
^^^^^^^^^^^^^^^^

要将使用PyWebIO编写的任务函数集成进Tornado应用，需要在Tornado应用中引入两个 ``RequestHandler`` ,
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
                  {"path": STATIC_PATH, 'default_filename': 'index.html'})
        ])
        application.listen(port=80, address='localhost')
        tornado.ioloop.IOLoop.current().start()

以上代码调用 `webio_handler(task_func) <pywebio.platform.webio_handler>` 来获得PyWebIO和浏览器进行通讯的Tornado ``RequestHandler`` ，
并将其绑定在 ``/tool/io`` 路径下；同时将PyWebIO的静态文件使用 ``tornado.web.StaticFileHandler`` 托管到 ``/tool/(.*)`` 路径下。
启动Tornado服务后，访问 ``http://localhost/tool/`` 即可使用PyWebIO服务

.. note::

   在Tornado中，PyWebIO使用WebSocket协议和浏览器进行通讯，所以，如果你的Tornado应用处在反向代理(比如Nginx)之后，
   可能需要特别配置反向代理来支持WebSocket协议，:ref:`这里 <nginx_ws_config>` 有一个Nginx配置WebSocket的例子。


与Flask集成
^^^^^^^^^^^^^^^^

和集成到Tornado相似，在与Flask集成的集成中，你也需要添加两个PyWebIO相关的路由：一个用来提供静态的前端文件，另一个用来和浏览器进行Http通讯::

    from pywebio.platform.flask import webio_view
    from pywebio import STATIC_PATH
    from flask import Flask, send_from_directory

    app = Flask(__name__)
    app.route('/io', methods=['GET', 'POST', 'OPTIONS'])(webio_view(task_func))

    @app.route('/')
    @app.route('/<path:static_file>')
    def serve_static_file(static_file='index.html'):
        return send_from_directory(STATIC_PATH, static_file)

    app.run(host='localhost', port=80)


.. _integration_web_framework_note:

注意事项
^^^^^^^^^^^

PyWebIO默认通过当前页面的同级的 ``./io`` API与后端进行通讯，比如如果你将PyWebIO静态文件托管到 ``/A/B/C/(.*)`` 路径下，那么你需要将
``webio_handler()`` 返回的 ``RequestHandler`` 绑定到 ``/A/B/C/io`` 处。如果你没有这样做的话，你需要在打开PyWebIO前端页面时，
传入 ``pywebio_api`` Url参数来指定PyWebIO后端API地址，比如 ``/A/B/C/?pywebio_api=/D/pywebio`` 将PyWebIO后端API地址设置到了
``/D/pywebio`` 处。 ``pywebio_api`` 参数可以使用相对地址、绝对地址甚至指定其他服务器。

如果你不想自己托管静态文件，你可以使用PyWebIO的Github Page页面: ``https://wang0618.github.io/PyWebIO/pywebio/html/?pywebio_api=`` ，需要在页面上通过 ``pywebio_api`` 参数传入后端API地址，并且将 ``https://wang0618.github.io`` 加入 ``allowed_origins`` 列表中（见下文说明）。

.. caution::

   需要注意 ``pywebio_api`` 参数的格式：
   相对地址可以为 ``./xxx/xxx`` 或 ``xxx/xxx`` 的格式
   绝对地址以 ``/`` 开头，比如 ``/aaa/bbb``
   指定其他服务器需要使用完整格式: ``ws://example.com:8080/aaa/io`` ,或者省略协议字段: ``//example.com:8080/aaa/io`` 。
   省略协议字段时，PyWebIO根据当前页面的协议确定要使用的协议: 若当前页面为http协议，则后端接口为ws协议；若当前页面为https协议，则后端接口为wss协议；

   当后端API与当前页面不再同一host下时，需要在 `webio_handler() <pywebio.platform.webio_handler>` 或
   `webio_view() <pywebio.platform.flask.webio_view>` 中使用 ``allowed_origins`` 或 ``check_origin``
   参数来允许后端接收页面所在的host

.. _coroutine_based_session:

基于协程的会话
---------------
PyWebIO的会话实现默认是基于线程的，用户每打开一个和服务端的会话连接，PyWebIO会启动一个线程来运行任务函数，你可以在会话中启动新的线程，通过 `register_thread(thread) <pywebio.session.register_thread>` 注册新创建的线程后新线程中也可以调用PyWebIO交互函数，当任务函数返回并且会话内所有的通过 `register_thread(thread) <pywebio.session.register_thread>` 注册的线程都退出后，会话结束。

除了基于线程的会话，PyWebIO还提供了基于协程的会话。基于协程的会话接受一个协程作为任务函数。

基于线程的会话为单线程模型，所有会话都运行在一个线程内。对于IO密集型的任务，协程比线程有更少的资源占用同时又拥有媲美于线程的性能。

要使用基于协程的会话，只需要在 `start_server() <pywebio.platform.start_server>` 中传入使用 ``async`` 声明的协程函数即可::

    from pywebio.input import *
    from pywebio.output import *
    from pywebio import start_server

    async def say_hello():
        name = await input("what's your name?")
        put_text('Hello, %s'%name)

    start_server(say_hello, auto_open_webbrowser=True)

在协程任务函数中，你可以使用 ``await`` 调用其他协程，也可以调用 `asyncio <https://docs.python.org/3/library/asyncio.html>`_ 库中的协程函数::

    import asyncio

    async def hello_word():
        put_text('Hello ...')
        await asyncio.sleep(1)
        put_text('... World!')

    async def main():
        await hello_word()
        put_text('Bye, bye')

    start_server(main, auto_open_webbrowser=True)

在基于协程的会话中，你可以启动线程，但是无法像基于线程的会话那样使用 `register_thread() <pywebio.session.register_thread>` 函数来使得在新线程内使用PyWebIO交互函数。
但你可以使用 `run_async(coro) <pywebio.session.run_async>` 来异步执行一个协程，新协程内可以使用PyWebIO交互函数::

    from pywebio.session import run_async

    async def counter(n):
        for i in range(n):
            put_text(i)
            await asyncio.sleep(1)

    async def main():
        run_async(counter(10))
        put_text('Bye, bye')


    start_server(main, auto_open_webbrowser=True)

`run_async(coro) <pywebio.session.run_async>` 返回一个 `TaskHandle <pywebio.session.coroutinebased.TaskHandle>` ，通过 ``TaskHandle`` 你可以查询协程运行状态和关闭协程。
与基于线程的会话类似，在基于协程的会话中，当任务函数和在会话内通过 ``run_async()`` 运行的协程全部结束后，会话关闭。

.. note::

   在基于协程的会话中， :doc:`pywebio.input </input>` 模块中的输入函数都需要使用 ``await`` 语法来获取返回值，
   忘记使用 ``await`` 将会是在使用基于协程的会话时常出现的错误。

   协程会话中，同样需要使用 ``await`` 语法来进行调用函数还有 :func:`pywebio.session.hold()`

与Web框架进行集成
^^^^^^^^^^^^^^^^^^^^^

基于协程的会话同样可以与Web框架进行集成，只需要在原来传入任务函数的地方改为传入协程函数即可。

但当前在使用基于协程的会话集成进Flask时，存在一些限制：

一是协程函数内还无法直接通过 ``await`` 直接调用asyncio库中的协程函数，目前需要使用
`run_asyncio_coroutine() <pywebio.session.run_asyncio_coroutine>` 进行包装。二是，在启动Flask服务器之前需要启动一个单独的线程来运行事件循环。

使用基于协程的会话集成进Flask的示例::

    import asyncio
    import threading
    from flask import Flask, send_from_directory
    from pywebio import STATIC_PATH
    from pywebio.output import *
    from pywebio.platform.flask import webio_view, run_event_loop
    from pywebio.session import run_asyncio_coroutine

    async def hello_word():
        put_text('Hello ...')
        await run_asyncio_coroutine(asyncio.sleep(1))
        put_text('... World!')

    app = Flask(__name__)
    app.add_url_rule('/io', 'webio_view', webio_view(hello_word), methods=['GET', 'POST', 'OPTIONS'])

    @app.route('/')
    @app.route('/<path:static_file>')
    def serve_static_file(static_file='index.html'):
        return send_from_directory(STATIC_PATH, static_file)
    
    threading.Thread(target=run_event_loop, daemon=True).start()
    app.run(host='localhost', port='80')

最后，使用PyWebIO编写的协程函数不支持Script mode，总是需要使用 ``start_server`` 来启动一个服务或者集成进Web框架来调用。