import json
import subprocess
from functools import partial
from os import path

import time
from percy import percySnapshot
from selenium.webdriver import Chrome

import pywebio
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *

proj_dir = path.dirname(path.dirname(path.abspath(__file__)))


def basic():
    set_auto_scroll_bottom(False)
    set_anchor('top')

    for i in range(3):
        put_text('text_%s' % i)

    put_text('测试空格:20空格:[%s]结束' % (' ' * 20))

    for i in range(3):
        put_text('inline_text_%s' % i, inline=True)

    put_markdown("""### put_markdown 测试
    `行内代码`
    
    无序列表：
    - 北京
    - 上海
    - 天津
     
    有序列表：
    1. 北京
    2. 上海
    3. 天津
    
    [链接](./#)
    ~~删除线~~
    """, strip_indent=4, anchor='put_markdown')

    put_text('put_html("<hr/>")')
    put_html("<hr/>", anchor='put_html')

    put_code(json.dumps(dict(name='pywebio', author='wangweimin'), indent=4), 'json', anchor='put_code')

    put_table([
        ['Name', 'Gender', 'Address'],
        ['Wang', 'M', 'China'],
        ['Liu', 'W', 'America'],
    ])

    put_table([
        ['Wang', 'M', 'China'],
        ['Liu', 'W', 'America'],
    ], header=['Name', 'Gender', 'Address'])

    put_table([
        {"Course": "OS", "Score": "80"},
        {"Course": "DB", "Score": "93"},
    ], header=["Course", "Score"], anchor='put_table')

    def edit_row(choice, row):
        put_text("You click %s button at row %s" % (choice, row), after='table_cell_buttons')

    put_table([
        ['Idx', 'Actions'],
        ['1', table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=1))],
        ['2', table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=2))],
        ['3', table_cell_buttons(['edit', 'delete'], onclick=partial(edit_row, row=3))],
    ], anchor='table_cell_buttons')

    put_buttons(['A', 'B', 'C'], onclick=partial(put_text, after='put_buttons'), anchor='put_buttons')

    put_image(open(proj_dir + "/docs/assets/input_1.png", 'rb').read(), anchor='put_image')

    put_file('hello_word.txt', b'hello word!', anchor='put_file')

    put_markdown('### 锚点')

    put_text('anchor A1', anchor='A1')
    put_text('new anchor A1', anchor='A1')
    put_text('anchor A2', anchor='A2')
    put_text('anchor A3', anchor='A3')

    put_text('after=A1', after='A1')
    put_text('after=A2', after='A2')
    put_text('before=A1', before='A1')
    put_text('before=A3', before='A3')
    put_text('after=A3', after='A3')

    clear_range('A1', "A2")
    clear_range('A3', 'A2')
    clear_after('A3')

    put_text('before=top', before='top')
    clear_before('top')
    put_text('before=top again', before='top')

    put_text('to remove', anchor='to_remove')
    remove('to_remove')

    hold()


def start_test_server():
    pywebio.enable_debug()
    start_server(basic, port=8080, debug=True, auto_open_webbrowser=False)


def test(server_proc: subprocess.Popen, browser: Chrome):
    btns = browser.find_elements_by_css_selector('#pywebio-anchor-put_buttons button')
    for btn in btns:
        btn.click()

    tab_btns = browser.find_elements_by_css_selector('#pywebio-anchor-table_cell_buttons button')
    for btn in tab_btns:
        btn.click()

    time.sleep(1)
    percySnapshot(browser=browser, name='basic output')


if __name__ == '__main__':
    import util

    util.run_test(start_test_server, test)
