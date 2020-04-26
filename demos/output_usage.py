"""
输出演示
^^^^^^^^^^^
演示PyWebIO支持的各种输出形式

:demo_host:`Demo地址 </?pywebio_api=output_usage>`  `源码 <https://github.com/wang0618/PyWebIO/blob/master/demos/output_usage.py>`_
"""
from pywebio import start_server
from pywebio.output import *
from pywebio.session import hold


def main():
    set_auto_scroll_bottom(False)
    set_title("PyWebIO输出演示")

    put_markdown("""# PyWebIO 输入演示
    
    在[这里](https://github.com/wang0618/PyWebIO/blob/master/demos/input_usage.py)可以获取本Demo的源码。
    
    PyWebIO的输出函数都定义在 `pywebio.output` 模块中，可以使用 `from pywebio.output import *` 引入。

    ### 基本输出
    PyWebIO提供了一些便捷函数来输出表格、链接等格式:
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
    
    PyWebIO提供的全部输出函数请参考PyWebIO文档
    """, strip_indent=4)
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

    put_markdown(r"""### 输出事件回调
    PyWebIO允许你输出一些控件，当控件被点击时执行提供的回调函数，就像编写GUI程序一样。
    
    下面是一个例子:
    ```python
    from functools import partial

    def edit_row(choice, row):
        put_markdown("> You click`%s` button ar row `%s`" % (choice, row))

    put_table([
        ['Idx', 'Actions'],
        [1, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])
    ```
    """, strip_indent=4)

    from functools import partial

    def edit_row(choice, row):
        put_markdown("> You click `%s` button ar row `%s`" % (choice, row), anchor='table-callback')

    put_table([
        ['Idx', 'Actions'],
        [1, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        [2, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        [3, table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ])
    set_anchor('table-callback')

    put_markdown(r"""当然，PyWebIO还支持单独的按钮控件:
    ```python
    def btn_click(btn_val):
        put_markdown("> You click `%s` button" % btn_val)

    put_buttons(['A', 'B', 'C'], onclick=btn_click)
    ```
    """, strip_indent=4)

    def btn_click(btn_val):
        put_markdown("> You click `%s` button" % btn_val, anchor='button-callback')

    put_buttons(['A', 'B', 'C'], onclick=btn_click)
    set_anchor('button-callback')

    put_markdown(r"""### 锚点
    就像在控制台输出文本一样，PyWebIO默认在页面的末尾输出各种内容，你可以使用锚点来改变这一行为。

    你可以调用 `set_anchor(name)` 对当前输出位置进行标记。
    
    你可以在任何输出函数中使用 `before` 参数将内容插入到指定的锚点之前，也可以使用 `after` 参数将内容插入到指定的锚点之后。
    
    在输出函数中使用 `anchor` 参数为当前的输出内容标记锚点，若锚点已经存在，则将锚点处的内容替换为当前内容。
    
    以下代码展示了在输出函数中使用锚点:
    ```python
    set_anchor('top')
    put_text('A')
    put_text('B', anchor='b')
    put_text('C', after='top')
    put_text('D', before='b')
    ```
    以上代码将输出:
    
        C
        A
        D
        B

    """, strip_indent=4)

    put_markdown(r"""### 页面环境设置
    #### 输出区外观
    PyWebIO支持两种外观：输出区固定高度/可变高度。 可以通过调用 `set_output_fixed_height(True)` 来开启输出区固定高度。
    
    #### 设置页面标题
    
    调用 `set_title(title)` 可以设置页面标题。
    
    #### 自动滚动
    
    在不指定锚点进行输出时，PyWebIO默认在输出完毕后自动将页面滚动到页面最下方；在调用输入函数时，也会将页面滚动到表单处。 通过调用 `set_auto_scroll_bottom(False)` 来关闭自动滚动。

    """, strip_indent=4)
    hold()


if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
