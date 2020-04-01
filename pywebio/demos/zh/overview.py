"""
使用PyWebIO来介绍PyWebIO的各个特性
"""

import asyncio
from datetime import datetime
from functools import partial

from pywebio import start_server, run_async, COROUTINE_BASED
from pywebio.input import *
from pywebio.output import *

import argparse


async def feature_overview():
    set_auto_scroll_bottom(False)
    set_output_fixed_height(False)
    set_title("PyWebIO 特性一览")

    put_markdown("""# PyWebIO 特性一览
    你现在看到和即将看到的内容就是使用PyWebIO来创建的，"用自己来介绍自己" 是不是很有趣 😄(文末有彩蛋)

    ## What is PyWebIO
    PyWebIO，一个用于在浏览器上进行输入输出的工具库。能够将原有的通过终端交互的脚本快速服务化，供其他人在网络通过浏览器使用；PyWebIO还可以方便地整合进现有的web服务，非常适合于构建后端服务的功能原型。

    特点：
    - 使用同步而不是基于回调的方式获取输入，无需在各个步骤之间保存状态，直观、方便
    - 代码侵入性小
    - 支持并发请求
    - 支持状态恢复
    - 支持整合到现有的web服务，目前支持与Tronado的集成

    对上面的内容一脸黑人问号，没关系，下面是一些PyWebIO是什么，以及能够做什么的直观的例子

    ### 基本输入
    首先是一些基本类型的输入

    #### 文本输入
    ```python
    age = await input("How old are you?", type=NUMBER)  # type can be in {TEXT, NUMBER, PASSWORD}
    ```
    这样一行代码的效果如下，浏览器会弹出一个文本输入框来获取输入，在你提交表单之前，你的程序不会往下运行
    """, lstrip=True)
    age = await input("How old are you?", type=NUMBER)
    put_text("你的年龄是：%s" % age)

    put_markdown("""#### 下拉选择框
    ```python
    gift = await select('Which gift you want?', ['keyboard', 'ipad'])
    ```
    """, lstrip=True)
    gift = await select('Which gift you want?', ['keyboard', 'ipad'])
    put_text("%s sounds great！" % gift)

    put_markdown("""#### CheckBox
    ```python
    agree = await checkbox("用户协议", options=['I agree to terms and conditions'])
    ```
    """, lstrip=True)
    agree = await checkbox("用户协议", options=[{'value': 'agree', 'label': 'I agree to terms and conditions'}])
    put_text("You %s to terms and conditions" % ('agree' if agree == 'agree' else 'disagree'))

    put_markdown("""#### Text Area
    ```python
    text = await textarea('Text Area', rows='3', placeholder='Some text')
    ```
    """, lstrip=True)
    text = await textarea('Text Area', rows='3', placeholder='Some text')
    put_text('Your input:%s' % text)

    put_markdown("""textarea还支持使用 <a href="https://codemirror.net/" target="_blank">Codemirror</a>实现代码风格的编辑区，只需使用`code`参数传入Codemirror支持的选项：
    ```python
    code = await textarea('Code', code={
        'mode': "python",  # 代码语言
        'theme': 'darcula',  # 使用darcula主题
    }, value='import something\n# Write your python code')
    ```
    """, lstrip=True)
    code = await textarea('Code', code={
        'mode': "python",  # 代码语言
        'theme': 'darcula',  # 使用darcula主题
    }, value='import something\n# Write your python code')
    put_markdown('Your code:\n```python\n%s\n```' % code)

    put_markdown("""#### Actions
    ```python
    choice = await actions("What do you want in next?", ["Go homepage", "Quit"])
    ```
    """, lstrip=True)
    choice = await actions("What do you want in next?", ["Go homepage", "Quit"])
    put_text("You choose %s" % choice)

    put_markdown("""#### 文件上传
    ```python
    img = await file_upload("Select a image:", accept="image/*")
    ```
    """, lstrip=True)
    img = await file_upload("Select a image:", accept="image/*")
    put_text("Image name: %s\nImage size: %d KB" % (img['filename'], len(img['content']) / 1000))

    put_markdown("""### 输入选项
    输入函数可指定的参数非常丰富，就比如：
    ```python
    await input('Help Text', type=TEXT, help_text='This is help text')
    ```
    """, lstrip=True)
    await input('Help Text', type=TEXT, help_text='This is help text')

    put_markdown("""```python
    await input('Placeholder', type=TEXT, placeholder='This is placeholder')
    ```
    """, lstrip=True)
    await input('Placeholder', type=TEXT, placeholder='This is placeholder')

    put_markdown("""```python
    await input('Readonly', type=TEXT, readonly=True, value="You can't change me")
    ```
    """, lstrip=True)
    await input('Readonly', type=TEXT, readonly=True, value="You can't change me")

    put_markdown("""我们可以为输入指定校验函数，校验函数校验通过时返回None，否则返回错误消息：
    ```python
    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = await input("How old are you?", type=NUMBER, valid_func=check_age)
    ```
    """, strip_indent=4)

    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息
        if p < 18:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = await input("How old are you?", type=NUMBER, valid_func=check_age, help_text='你可以输入一些不合法的数字(比如10)来查看错误提示的效果')

    put_markdown("""### 输入组
    PyWebIO还支持一组输入, 返回结果为一个字典。input_group接受前面的单项输入组成的列表作为参数，同时为了在返回的结果中区别出每一项输入，还需要在单项输入函数中传入`name`参数，input_group返回的字典就是以单项输入函数中的`name`作为键。
    ```python
    data = await input_group("Basic info",[
      input('Input your name', name='name'), 
      input('Input your age', name='age', type=NUMBER, valid_func=check_age)
    ], valid_func=check_form)
    print(data['name'], data['age'])
    ```
    输入组中同样支持设置校验函数，其接受整个表单数据作为参数：
    ```python
    def check_form(data):  # 检验函数校验通过时返回None，否则返回 (input name,错误消息)
        if len(data['name']) > 6:
            return ('name', '名字太长！')
        if data['age'] <= 0:
            return ('age', '年龄不能为负数！')
    ```
    """, strip_indent=4)

    def check_form(data):  # 检验函数校验通过时返回None，否则返回 (input name,错误消息)
        """返回 (name, error_msg) 表示输入错误"""  # todo 也可返回单独error_msg表示错误消息
        if len(data['name']) > 6:
            return ('name', '名字太长！')
        if data['age'] <= 0:
            return ('age', '年龄不能为负数！')

    data = await input_group("Basic info", [
        input('Input your name', name='name'),
        input('Input your age', name='age', type=NUMBER, valid_func=check_age)
    ], valid_func=check_form)
    put_text('Your name:%s\nYour age:%d' % (data['name'], data['age']))

    put_markdown("""### 输出
    PyWebIO也提供了一些便捷函数来输出表格，链接等格式
    #### 基本输出
    首先是文本输出：
    ```python
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
    ```
    """, strip_indent=4)
    put_text("Hello world!")
    put_table([
        ['商品', '价格'],
        ['苹果', '5.5'],
        ['香蕉', '7'],
    ])
    put_markdown('~~删除线~~')
    put_file('hello_word.txt', b'hello word!')

    put_markdown("""#### 输出事件
    通过刚刚的体验，相信聪明的你已经大概了解：PyWebIO可以通过调用不同的输入函数在浏览器中获取用户的输入，并且通过浏览器展示程序的输出。并且一旦调用 `await some_input_func()`，在表单提交之前程序将不会往下运行。
    这种模式已经可以满足绝大部分的交互需求了，但是在某些场景下还是显得不太方便，就比如你通过表格输出了用户的登陆日志，用户可能希望对表格的某些行进行编辑或者对表格什么也不做，这个时候，你可能会使用一个`while`循环，并且在循环中调用`choice = await actions("What do you want in next?", ["Edit some rows", "Back"])`，如果用户选择了"Edit some rows"，你还要接着询问用户希望编辑哪些行......，emm，想想就头大。
    幸运的是，PyWebIO还支持输出可以绑定事件的按钮控件，非常适合上述场景的需求。
    上述场景通过按钮控件实现如下：
    ```python
    from functools import partial
    
    def edit_row(choice, row):
        put_text("You click %s button ar row %s" % (choice, row))

    put_table([
        ['Idx', 'Actions'],
        [1, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])
    ```
    """, strip_indent=4)

    def edit_row(choice, row):
        put_text("You click %s button ar row %s" % (choice, row))

    put_table([
        ['Idx', 'Actions'],
        [1, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])
    put_markdown("""这样，你不必等待用户点击某个按钮，而是可以继续往下运行程序，当用户点击了某行中的按钮时，程序会自动调用相应的处理函数\n
    当然，PyWebIO还支持单独的按钮控件：
    ```python
    def btn_click(btn_val):
        put_text("You click btn_val button" % btn_val)
    put_buttons(['A', 'B', 'C'], onclick=btn_click)
    ```
    """, strip_indent=4)

    def btn_click(btn_val):
        put_text("You click %s button" % btn_val)

    put_buttons(['A', 'B', 'C'], onclick=btn_click)

    await actions('', ['继续教程'])

    put_markdown("""#### 锚点
    你可以调用`set_anchor(name)`对当前输出位置进行标记，这一调用不会在用户浏览器上产生任何输出，需要与下面几个函数结合使用：
    调用`set_anchor(name)`可以清除anchor锚点之前输出的内容
    调用`clear_after(name)`可以清除anchor锚点之后输出的内容
    调用`clear_range(start_anchor, end_ancher)`可以清除start_anchor到end_ancher锚点之间的内容
    调用`scroll_to(name)`可以将页面滚动到anchor锚点处
    """, strip_indent=4)

    set_anchor('anchor')
    put_markdown("""这个例子展示了锚点的一个用法：
    ```python
    import asyncio
    from datetime import datetime

    set_anchor('counter')
    for i in range(15, -1, -1):
        clear_after('counter')
        put_text('倒计时:%s' % i)
        await asyncio.sleep(1)  # 睡眠一秒钟
    ```
    """, strip_indent=4)
    await actions('点击开始示例', ['开始示例'])
    set_anchor('counter')
    for i in range(5, -1, -1):
        clear_after('counter')
        put_text('倒计时:%s' % i)
        await asyncio.sleep(1)  # 睡眠一秒钟

    put_markdown("""#### 环境设置
    ##### 输出区外观
    PyWebIO支持两种外观：输出区固定高度/可变高度。
    可以通过调用`set_output_fixed_height(True)`来开启输出区固定高度。\n
    你现在看到的是输出区可变高度的形态，你可以点击下面的按钮来切换外观。
    """, strip_indent=4)
    put_buttons([
        {'label': '输出区固定高度', 'value': 'fixed'},
        {'label': '输出区可变高度', 'value': 'no-fix'}
    ], lambda i: set_output_fixed_height(i == 'fixed'), small=True)

    put_markdown("""不过你最好在程序一开始就设置好输出区外观，否则你可能就会像现在这样手足无措～

    调用`set_title(title)`可以设置标题。\n
    """, strip_indent=4)

    async def set_title_btn(data):
        title = await input("Input title")
        set_title(title)

    put_buttons(['设置标题'], onclick=set_title_btn)

    await actions('', ['继续教程'])

    put_markdown("""##### 自动滚动
    通过调用`set_auto_scroll_bottom(True)`来开启自动滚动，当有新内容输出时会自动将页面滚动到底部。\n
    """, strip_indent=4)
    put_buttons([
        {'label': '开启自动滚动', 'value': 'enable'},
        {'label': '关闭自动滚动', 'value': 'disable'}
    ], lambda i: set_auto_scroll_bottom(i == 'enable'), small=True)

    put_markdown("""#### Async
    由于PyWebIO是基于Tornado构建的，而Tornado又与Python标准库<a href="https://docs.python.org/3/library/asyncio.html" target="_blank">asyncio</a>兼容，所以在PyWebIO中，你也可以运行`asyncio`中的协程函数

    这一点其实在上文已经出现过了，不记得了？
    """, strip_indent=4)
    put_buttons(['点此穿越🚀'], onclick=lambda _: scroll_to('anchor'))

    #
    put_markdown("""
    上文中的例子，之所以要使用asyncio中的sleep函数而不是Python `time`标准库中的sleep函数，是因为Tornado以及`asyncio`实际上是一个单线程模型，当前协程当进行一些需要等待的操作时，可以使用`await`让出程序控制权，框架会选择协程授予执行控制权，而调用`time.sleep`并不会让出程序控制权，因此在程序等待的间隔内，其他协程无法得到执行。更具体的关于协程以及asyncio的讨论已经超出了PyWebIO的范畴，你可以取互联网搜索相关内容来进行了解。

    回到PyWebIO，你也可以`await`自己编写的协程函数
    ```python
    import asyncio

    async def request():
        http_client = AsyncHTTPClient()
        response = await http_client.fetch("http://example.com")
        put_text(response.body)
        return response

    response = await request()
    ```

    `run_async`允许你在一个协程函数中在后台启动另一个协程函数，不会像使用`await`一样阻塞当前协程，当前协程可以继续往下执行。

    ```python
    import asyncio
    from datetime import datetime

    async def show_time():
        text = await input("来自后台协程的输入请求", placeholder='随便输入点啥')
        put_text('你刚刚输入了:%s' % text)
        for _ in range(10):
            put_text('来自后台协程的报时:%s' % datetime.now())
            await asyncio.sleep(1)

    run_async(show_time())
    
    for i in range(5, -1, -1):
        put_text('来自主协程的倒计时:%s' % i)
        await asyncio.sleep(1)
    
    ```

    在新生成的协程内，依然可以调用输入函数，若用户当前已经有正在展示的输入表单，则会被新生成的表单替换，但是旧表单不会被销毁，旧表单的输入状态也会保留，当新表单提交后，旧输入表单会重新呈现给用户。
    """, strip_indent=4)

    async def show_time():
        text = await input("来自后台协程的输入请求", placeholder='随便输入点啥')
        put_text('你刚刚输入了:%s' % text)
        for _ in range(10):
            put_text('来自后台协程的报时:%s' % datetime.now())
            await asyncio.sleep(1)

    await actions('', ['运行run_async(show_time())'])

    run_async(show_time())

    for i in range(15, -1, -1):
        put_text('来自主协程的倒计时:%s' % i)
        await asyncio.sleep(1)

    await asyncio.sleep(2)

    put_markdown("""
    <hr/>

    以上大概就是 PyWebIO 的所有特性了，如果觉得还不错的话，可以 Give me a 🌟 in <a href="https://github.com/wang0618/PyWebIO" target="_blank">Github</a>

    PS： <a href="https://github.com/wang0618/PyWebIO/blob/master/pywebio/demos/overview-zh.py" target="_blank">在这里</a>你可以找到生成本页面的脚本
    PPS：开头提到的彩蛋揭晓："用自己来介绍自己"很具计算机领域风格，对此发挥至极的是<a href="https://en.wikipedia.org/wiki/Quine_(computing)" target="_blank">Quine</a>的概念，"A quine is a program which prints a copy of its own as the only output. "
    """, strip_indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PyWebIO Overview demo')
    parser.add_argument('--host', default='localhost', help='server bind host')
    parser.add_argument('--port', type=int, default=0, help='server bind port')
    args = parser.parse_args()

    # from pywebio.platform.flask import start_server
    start_server(feature_overview, debug=1, host=args.host, port=args.port, allowed_origins=['http://localhost:63342'])
