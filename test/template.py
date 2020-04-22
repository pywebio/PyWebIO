import asyncio
import json
import os
import threading
from functools import partial
from os import path

import time
from percy import percySnapshot
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import Select

from pywebio.input import *
from pywebio.output import *
from pywebio.session import *

here_dir = path.dirname(path.abspath(__file__))


def get_visible_form(browser):
    forms = browser.find_elements_by_css_selector('#input-container > div')
    for f in forms:
        if f.is_displayed():
            return f


def basic_output():
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
    """, lstrip=True, anchor='put_markdown')

    put_text('<hr/>:')
    put_html("<hr/>", anchor='put_html')

    put_text('code:')
    put_code(json.dumps(dict(name='pywebio', author='wangweimin'), indent=4), 'json', anchor='put_code')

    put_text('table:')
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

    img_data = open(path.join(here_dir, 'assets', 'img.png'), 'rb').read()
    put_image(img_data, anchor='put_image1')
    put_image(img_data, width="30px", anchor='put_image2')
    put_image(img_data, height="50px", anchor='put_image3')

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


def background_output():
    put_text("Background output", anchor='background')

    def background():
        for i in range(20):
            put_text('%s ' % i, inline=True, after='background')

    t = threading.Thread(target=background)
    register_thread(t)
    t.start()


async def coro_background_output():
    put_text("Background output", anchor='background')

    async def background():
        for i in range(20):
            put_text('%s ' % i, inline=True, after='background')

    return run_async(background())


def test_output(browser: Chrome, percy_prefix=''):
    """测试输出::

        template.basic_output()
        template.background_output() # 或者 await template.coro_background_output()
        hold()

    """
    time.sleep(1)  # 等待输出完毕

    if percy_prefix:
        percy_prefix = percy_prefix + ' '

    tab_btns = browser.find_elements_by_css_selector('#pywebio-anchor-table_cell_buttons button')
    for btn in tab_btns:
        time.sleep(0.5)
        btn.click()

    btns = browser.find_elements_by_css_selector('#pywebio-anchor-put_buttons button')
    for btn in btns:
        time.sleep(0.5)
        btn.click()

    time.sleep(1)
    percySnapshot(browser=browser, name=percy_prefix + 'basic output')


def basic_input():
    age = yield input("How old are you?", type=NUMBER)
    put_markdown(f'`{repr(age)}`')

    password = yield input("Input password", type=PASSWORD)
    put_markdown(f'`{repr(password)}`')

    # 下拉选择框
    gift = yield select('Which gift you want?', ['keyboard', 'ipad'])
    put_markdown(f'`{repr(gift)}`')

    # CheckBox
    agree = yield checkbox("用户协议", options=['I agree to terms and conditions'])
    put_markdown(f'`{repr(agree)}`')

    # Text Area
    text = yield textarea('Text Area', rows=3, placeholder='Some text')
    put_markdown(f'`{repr(text)}`')

    # 文件上传
    img = yield file_upload("Select a image:", accept="image/*")
    put_markdown(f'`{repr(img)}`')

    # 输入参数
    res = yield input('This is label', type=TEXT, placeholder='This is placeholder,required=True',
                      help_text='This is help text', required=True)
    put_markdown(f'`{repr(res)}`')

    # 校验函数
    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = yield input("How old are you?", type=NUMBER, valid_func=check_age, help_text='age in [10, 60]')
    put_markdown(f'`{repr(age)}`')

    # Codemirror
    code = yield textarea('Code Edit', code={
        'mode': "python",  # 编辑区代码语言
        'theme': 'darcula',  # 编辑区darcula主题, Visit https://codemirror.net/demo/theme.html#cobalt to get more themes
    }, value='import something\n# Write your python code')
    put_markdown(f'`{repr(code)}`')

    # 输入组
    info = yield input_group("Cancelable", [
        input('Input your name', name='name'),
        input('Input your age', name='age', type=NUMBER, valid_func=check_age, help_text='age in [10, 60]')
    ], cancelable=True)
    put_markdown(f'`{repr(info)}`')

    def check_form(data):  # 检验函数校验通过时返回None，否则返回 (input name,错误消息)
        if len(data['password']) > 6:
            return ('password', 'password太长！')

    check_item_data = []

    def check_item(data):
        check_item_data.append(repr(data))

    info = yield input_group('Input group', [
        input('Text', type=TEXT, datalist=['data-%s' % i for i in range(10)], name='text',
              required=True, help_text='required=True', valid_func=check_item),
        input('Number', type=NUMBER, value="42", name='number', valid_func=check_item),
        input('Float', type=FLOAT, name='float', valid_func=check_item),
        input('Password', type=PASSWORD, name='password', valid_func=check_item),

        textarea('Textarea', rows=3, maxlength=20, name='textarea',
                 help_text='rows=3, maxlength=20', valid_func=check_item),

        textarea('Code', name='code', code={
            'lineNumbers': False,
            'indentUnit': 2,
        }, value='import something\n# Write your python code', valid_func=check_item),

        select('select-multiple', [
            {'label': '标签0,selected', 'value': '0', 'selected': True},
            {'label': '标签1,disabled', 'value': '1', 'disabled': True},
            ('标签2,selected', '2', True),
            ('标签3', '3'),
            ('标签4,disabled', '4', False, True),
            '标签5,selected',
        ], name='select-multiple', multiple=True, value=['标签5,selected'], required=True,
               help_text='required至少选择一项', valid_func=check_item),

        select('select', [
            {'label': '标签0', 'value': '0', 'selected': False},
            {'label': '标签1,disabled', 'value': '1', 'disabled': True},
            ('标签2', '2', False),
            ('标签3', '3'),
            ('标签4,disabled', '4', False, True),
            '标签5,selected',
        ], name='select', value=['标签5,selected'], valid_func=check_item),

        checkbox('checkbox-inline', [
            {'label': '标签0,selected', 'value': '0', 'selected': False},
            {'label': '标签1,disabled', 'value': '1', 'disabled': True},
            ('标签2,selected', '2', True),
            ('标签3', '3'),
            ('标签4,disabled', '4', False, True),
            '标签5,selected',
        ], inline=True, name='checkbox-inline', value=['标签5,selected', '标签0', '标签0,selected'], valid_func=check_item),

        checkbox('checkbox', [
            {'label': '标签0,selected', 'value': '0', 'selected': True},
            {'label': '标签1,disabled', 'value': '1', 'disabled': True},
            ('标签2,selected', '2', True),
            ('标签3', '3'),
            ('标签4,disabled', '4', False, True),
            '标签5',
        ], name='checkbox', valid_func=check_item),

        radio('radio-inline', [
            {'label': '标签0', 'value': '0', 'selected': False},
            {'label': '标签1,disabled', 'value': '1', 'disabled': True},
            ('标签2', '2', False),
            ('标签3', '3'),
            ('标签4,disabled', '4', False, True),
            '标签5,selected',
        ], inline=True, name='radio-inline', value='标签5,selected', valid_func=check_item),

        radio('radio', [
            {'label': '标签0', 'value': '0', 'selected': False},
            {'label': '标签1,disabled', 'value': '1', 'disabled': True},
            ('标签2', '2', False),
            ('标签3', '3'),
            ('标签4,disabled', '4', False, True),
            '标签5,selected',
        ], inline=False, name='radio', value='标签5,selected', valid_func=check_item),

        file_upload('file_upload', name='file_upload'),

        actions('actions', [
            {'label': '提交', 'value': 'submit'},
            ('提交2', 'submit2'),
            '提交3',
            {'label': 'disabled', 'disabled': True},
            ('重置', 'reset', 'reset'),
            {'label': '取消', 'type': 'cancel'},
        ], name='actions', help_text='actions'),

    ], valid_func=check_form)

    put_text('`valid_func()` log:')
    put_code(json.dumps(sorted(check_item_data), indent=4, ensure_ascii=False), 'json')

    put_text('Form result:')
    if info:
        put_code(json.dumps([repr(i) for i in sorted(info.items())], indent=4, ensure_ascii=False), 'json')

    # yield actions(['Continue'])


def background_input():
    def background():
        time.sleep(1)
        res = input('background')
        put_markdown(f'`background: {repr(res)}`')

    t = threading.Thread(target=background)
    register_thread(t)
    t.start()

    res = input('front')
    put_markdown(f'`front: {repr(res)}`')


async def coro_background_input():
    async def background():
        await asyncio.sleep(1)
        res = await input('background')
        put_markdown(f'`background: {repr(res)}`')

    run_async(background())

    res = await input('front')
    put_markdown(f'`front: {repr(res)}`')


async def flask_coro_background_input():
    async def background():
        await run_asyncio_coroutine(asyncio.sleep(1))
        res = await input('background')
        put_markdown(f'`background: {repr(res)}`')

    run_async(background())

    res = await input('front')
    put_markdown(f'`front: {repr(res)}`')


def test_input(browser: Chrome, percy_prefix=''):
    """测试输入::

        template.basic_input()
        actions(['Continue'])
        template.background_input() # 或者 await template.coro_background_input() / flask_coro_background_input

    """
    if percy_prefix:
        percy_prefix = percy_prefix + ' '

    browser.find_element_by_css_selector('input').send_keys("22")
    browser.find_element_by_tag_name('form').submit()

    time.sleep(0.5)
    browser.find_element_by_css_selector('input').send_keys("secret")
    browser.find_element_by_tag_name('form').submit()

    time.sleep(0.5)
    browser.find_element_by_tag_name('form').submit()

    # checkbox
    time.sleep(0.5)
    browser.find_element_by_css_selector('input').click()
    browser.find_element_by_tag_name('form').submit()

    # Text Area
    time.sleep(0.5)
    browser.find_element_by_css_selector('textarea').send_keys(" ".join(str(i) for i in range(20)))
    browser.find_element_by_tag_name('form').submit()

    # file
    time.sleep(0.5)
    img_path = path.join(here_dir, 'assets', 'img.png')
    browser.find_element_by_css_selector('input').send_keys(img_path)
    browser.find_element_by_tag_name('form').submit()

    # text
    time.sleep(0.5)
    browser.find_element_by_css_selector('input').send_keys("text")
    browser.find_element_by_tag_name('form').submit()

    # valid func, age in [10, 60]
    time.sleep(0.5)
    browser.find_element_by_css_selector('input').send_keys("1")
    browser.find_element_by_tag_name('form').submit()
    time.sleep(0.5)
    browser.find_element_by_css_selector('input').clear()
    browser.find_element_by_css_selector('input').send_keys("90")
    browser.find_element_by_tag_name('form').submit()
    time.sleep(0.5)
    browser.find_element_by_css_selector('input').clear()
    browser.find_element_by_css_selector('input').send_keys("23")
    browser.find_element_by_tag_name('form').submit()

    # code
    time.sleep(0.5)
    # browser.find_element_by_css_selector('textarea').send_keys(" ".join(str(i) for i in range(20)))
    browser.find_element_by_tag_name('form').submit()

    # Cancelable from group
    time.sleep(0.5)
    browser.find_element_by_css_selector('input[name="name"]').send_keys("name")
    browser.find_element_by_css_selector('input[name="age"]').send_keys("90")
    browser.find_element_by_tag_name('form').submit()
    percySnapshot(browser=browser, name=percy_prefix + 'input group invalid')
    browser.find_element_by_css_selector('input[name="age"]').clear()
    browser.find_element_by_css_selector('input[name="age"]').send_keys("23")
    browser.find_element_by_tag_name('form').submit()

    # Input group
    time.sleep(0.5)
    percySnapshot(browser=browser, name=percy_prefix + 'input group all')
    browser.find_element_by_css_selector('input[name="text"]').send_keys("name")
    browser.find_element_by_css_selector('input[name="number"]').send_keys("20")
    browser.find_element_by_css_selector('input[name="float"]').send_keys("3.1415")
    browser.find_element_by_css_selector('input[name="password"]').send_keys("password")
    browser.find_element_by_css_selector('textarea[name="textarea"]').send_keys(" ".join(str(i) for i in range(20)))
    # browser.find_element_by_css_selector('[name="code"]').send_keys(" ".join(str(i) for i in range(10)))
    Select(browser.find_element_by_css_selector('select[name="select-multiple"]')).select_by_index(0)
    # browser. find_element_by_css_selector('[name="select"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="checkbox-inline"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="checkbox"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="radio-inline"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="radio"]'). send_keys("name")
    browser.find_element_by_css_selector('input[name="file_upload"]').send_keys(img_path)

    browser.find_element_by_css_selector('button[value="submit2"]').click()
    time.sleep(0.5)
    percySnapshot(browser=browser, name=percy_prefix + 'input group all invalid')

    browser.find_element_by_css_selector('input[name="password"]').clear()
    browser.find_element_by_css_selector('input[name="password"]').send_keys("123")
    browser.find_element_by_css_selector('button[value="submit2"]').click()
    time.sleep(0.5)
    percySnapshot(browser=browser, name=percy_prefix + 'input group all submit')

    browser.find_element_by_css_selector('form').submit()

    # background
    time.sleep(3)
    get_visible_form(browser).find_element_by_css_selector('input').send_keys("background")
    get_visible_form(browser).find_element_by_tag_name('form').submit()
    # front
    time.sleep(0.5)
    get_visible_form(browser).find_element_by_css_selector('input').send_keys("front")
    get_visible_form(browser).find_element_by_tag_name('form').submit()


def set_defer_call():
    def deferred_1():
        open('test_defer.tmp', 'w').write('deferred_1')

    def deferred_2():
        open('test_defer.tmp', 'a').write('deferred_2')

    defer_call(deferred_1)
    defer_call(deferred_2)


def test_defer_call():
    output = open('test_defer.tmp').read()
    assert "deferred_1" in output
    assert "deferred_2" in output

    os.remove('test_defer.tmp')
