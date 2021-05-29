"""
Input demo
^^^^^^^^^^^^^^^
Demonstrate various input usage supported by PyWebIO

:demo_host:`Demo </input_usage>`, `Source code <https://github.com/wang0618/PyWebIO/blob/dev/demos/input_usage.py>`_
"""
import json

from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import set_env, info as session_info


def t(eng, chinese):
    """return English or Chinese text according to the user's browser language"""
    return chinese if 'zh' in session_info.user_language else eng


def main():
    """PyWebIO Input Usage

    Demonstrate various input usage supported by PyWebIO.
    演示PyWebIO输入模块的使用
    """
    set_env(auto_scroll_bottom=True)

    put_markdown(t("""# PyWebIO Input Example
    
    You can get the source code of this demo in [here](https://github.com/wang0618/PyWebIO/blob/dev/demos/input_usage.py)
    
    This demo only introduces part of the functions of the PyWebIO input module. For the complete features, please refer to the [User Guide](https://pywebio.readthedocs.io/zh_CN/latest/guide.html).
    
    The input functions are all defined in the `pywebio.input` module and can be imported using `from pywebio.input import *`.
    
    ### Basic input
    Here are some basic types of input.
    
    #### Text input
    ```python
    name = input("What's your name?")
    ```
    """,
    """# PyWebIO 输入演示
    
    在[这里](https://github.com/wang0618/PyWebIO/blob/dev/demos/input_usage.py)可以获取本Demo的源码。
    
    本Demo仅提供了PyWebIO输入模块的部分功能的演示，完整特性请参阅[用户指南](https://pywebio.readthedocs.io/zh_CN/latest/guide.html)。
    
    PyWebIO的输入函数都定义在 `pywebio.input` 模块中，可以使用 `from pywebio.input import *` 引入。

    ### 基本输入
    首先是一些基本类型的输入

    #### 文本输入
    ```python
    name = input("What's your name?")
    ```
    """), lstrip=True)
    put_text(t("The results of the above example are as follows:", "这样一行代码的效果如下："))
    name = input("What's your name?")
    put_markdown("`name = %r`" % name)

    # 其他类型的输入
    put_markdown(t("""
    PyWebIO’s input functions is blocking and will not return until the form is successfully submitted.
    #### Other types of input
    Here are some other types of input functions:
    ```python
    # Password input
    password = input("Input password", type=PASSWORD)
    
    # Drop-down selection
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    
    # CheckBox
    agree = checkbox("User Term", options=['I agree to terms and conditions'])
    
    # Text Area
    text = textarea('Text Area', rows=3, placeholder='Some text')
    
    # File Upload
    img = file_upload("Select a image:", accept="image/*")
    ```
    """, """
    PyWebIO的输入函数是同步的，在表单被提交之前，输入函数不会返回。
    #### 其他类型的输入:
    ```python
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
    ```
    """), lstrip=True)
    password = input("Input password", type=PASSWORD)
    put_markdown("`password = %r`" % password)
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    put_markdown("`gift = %r`" % gift)
    agree = checkbox(t("User Term", "用户协议"), options=['I agree to terms and conditions'])
    put_markdown("`agree = %r`" % agree)
    text = textarea('Text Area', rows=3, placeholder='Some text')
    put_markdown("`text = %r`" % text)
    img = file_upload("Select a image:", accept="image/*", help_text=t('You can just click "Submit" button', '可以直接选择"提交"'))
    if img is None:
        put_markdown("`img = %r`" % img)
    else:
        img['content'] = '...'
        img.pop('dataurl', None)
        put_code(json.dumps(img, indent=4, ensure_ascii=False).replace('"..."', '...'), 'json')

    # 输入选项
    put_markdown(t("""#### Parameter of input functions
    There are many parameters that can be passed to the input function:
    """, """#### 输入选项
    输入函数可指定的参数非常丰富：
    """), strip_indent=4)
    put_markdown("""
    ```python
    input('This is label', type=TEXT, placeholder='This is placeholder', 
          help_text='This is help text', required=True, 
          datalist=['candidate1', 'candidate2', 'candidate2'])
    ```
    """, strip_indent=4)
    input('This is label', type=TEXT, placeholder='This is placeholder',
          help_text='This is help text', required=True,
          datalist=['candidate1', 'candidate2', 'candidate2'])

    # 校验函数
    put_markdown(t("""You can specify a validation function for the input by using `validate` parameter. The validation function should return `None` when the check passes, otherwise an error message will be returned:""", """我们可以为输入指定校验函数，校验函数校验通过时返回`None`，否则返回错误消息:"""), strip_indent=4)
    put_markdown("""
    ```python
    def check_age(p):  # return None when the check passes, otherwise return the error message
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = input("How old are you?", type=NUMBER, validate=check_age)
    ```
    """, strip_indent=4)

    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = input("How old are you?", type=NUMBER, validate=check_age, help_text=t('Try to input some illegal values, such as "8", "65"','尝试输入一些非法值，比如"8"、"65"'))
    put_markdown('`age = %r`' % age)

    # Codemirror
    put_markdown(t("""You can use `code` parameter in `pywebio.input.textarea()` to create a code editing textarea:""", """PyWebIO 的 `textarea()` 输入函数还支持使用 [Codemirror](https://codemirror.net/) 实现代码风格的编辑区，只需使用 `code` 参数传入Codemirror支持的选项即可(最简单的情况是直接传入` code={}` 或 `code=True`):"""), strip_indent=4)
    put_markdown(r"""
    ```python
    code = textarea('Code Edit', code={
        'mode': "python",  # code language
        'theme': 'darcula',  #  Codemirror theme
    }, value='import something\n# Write your python code')
    ```
    """, strip_indent=4)

    code = textarea('Code Edit', code={
        'mode': "python",  # 编辑区代码语言
        'theme': 'darcula',  # 编辑区darcula主题, Visit https://codemirror.net/demo/theme.html#cobalt to get more themes
    }, value='import something\n# Write your python code')

    put_markdown("Your code:\n```python\n%s\n```" % code)

    # 输入组
    put_markdown(t("""### Input Group
    `input_group()` accepts a list of single input function call as parameter, and returns a dictionary with the name of the single input function as the key and the input data as the value.
    The input group also supports using `validate` parameter to set the validation function, which accepts the entire form data as parameter:""",
    """### 输入组
    `input_group()` 接受单项输入组成的列表作为参数，输入组中需要在每一项输入函数中提供 `name` 参数来用于在结果中标识不同输入项。输入组中同样支持设置校验函数，其接受整个表单数据作为参数。检验函数校验通过时返回None，否则返回 `(input name,错误消息)`
    """), strip_indent=4)
    put_markdown(r"""
    ```python
    def check_form(data):  # input group validation: return (input name, error msg) when validation fail
        if len(data['name']) > 6:
            return ('name', 'Name too long!')
        if data['age'] <= 0:
            return ('age', 'Age can not be negative!')

    data = input_group("Basic info", [
        input('Input your name', name='name'),
        input('Input your age', name='age', type=NUMBER, validate=check_age)
    ], validate=check_form)
    ```
    """, strip_indent=4)

    def check_form(data):  # input group validation: return (input name, error msg) when validation fail
        if len(data['name']) > 6:
            return ('name', 'Name too long!')
        if data['age'] <= 0:
            return ('age', 'Age can not be negative!')

    data = input_group("Basic info", [
        input('Input your name', name='name'),
        input('Input your age', name='age', type=NUMBER, validate=check_age)
    ], validate=check_form)

    put_markdown("`data = %r`" % data)

    put_markdown(t("""----
    For more information about input of PyWebIO, please visit PyWebIO [User Guide](https://pywebio.readthedocs.io/zh_CN/latest/guide.html) and [input module documentation](https://pywebio.readthedocs.io/zh_CN/latest/input.html).
    """, """----
    PyWebIO的输入演示到这里就结束了，更多内容请访问PyWebIO[用户指南](https://pywebio.readthedocs.io/zh_CN/latest/guide.html)和[input模块文档](https://pywebio.readthedocs.io/zh_CN/latest/input.html)。
    """), lstrip=True)


if __name__ == '__main__':
    start_server(main, debug=True, port=8080, cdn=False)
