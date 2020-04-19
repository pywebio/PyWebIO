import json
import subprocess
import time
from percy import percySnapshot
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import Select

import pywebio
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *

from os import path

here_dir = path.dirname(path.abspath(__file__))


def basic():
    set_auto_scroll_bottom(True)

    age = input("How old are you?", type=NUMBER)
    put_markdown(f'`{repr(age)}`')

    password = input("Input password", type=PASSWORD)
    put_markdown(f'`{repr(password)}`')

    # 下拉选择框
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    put_markdown(f'`{repr(gift)}`')

    # CheckBox
    agree = checkbox("用户协议", options=['I agree to terms and conditions'])
    put_markdown(f'`{repr(agree)}`')

    # Text Area
    text = textarea('Text Area', rows=3, placeholder='Some text')
    put_markdown(f'`{repr(text)}`')

    # 文件上传
    img = file_upload("Select a image:", accept="image/*")
    put_markdown(f'`{repr(img)}`')

    # 输入参数
    res = input('This is label', type=TEXT, placeholder='This is placeholder,required=True',
                help_text='This is help text', required=True)
    put_markdown(f'`{repr(res)}`')

    # 校验函数
    def check_age(p):  # 检验函数校验通过时返回None，否则返回错误消息
        if p < 10:
            return 'Too young!!'
        if p > 60:
            return 'Too old!!'

    age = input("How old are you?", type=NUMBER, valid_func=check_age, help_text='age in [10, 60]')
    put_markdown(f'`{repr(age)}`')

    # Codemirror
    code = textarea('Code Edit', code={
        'mode': "python",  # 编辑区代码语言
        'theme': 'darcula',  # 编辑区darcula主题, Visit https://codemirror.net/demo/theme.html#cobalt to get more themes
    }, value='import something\n# Write your python code')
    put_markdown(f'`{repr(code)}`')

    # 输入组
    info = input_group("Cancelable", [
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

    info = input_group('Input group', [
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


def start_test_server():
    pywebio.enable_debug()
    start_server(basic, port=8080, debug=False, auto_open_webbrowser=False)


def test(server_proc: subprocess.Popen, browser: Chrome):
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
    percySnapshot(browser=browser, name='input group invalid')
    browser.find_element_by_css_selector('input[name="age"]').clear()
    browser.find_element_by_css_selector('input[name="age"]').send_keys("23")
    browser.find_element_by_tag_name('form').submit()

    # Input group
    time.sleep(0.5)
    percySnapshot(browser=browser, name='input group all')
    browser.find_element_by_css_selector('[name="text"]').send_keys("name")
    browser.find_element_by_css_selector('[name="number"]').send_keys("20")
    browser.find_element_by_css_selector('[name="float"]').send_keys("3.1415")
    browser.find_element_by_css_selector('[name="password"]').send_keys("password")
    browser.find_element_by_css_selector('[name="textarea"]').send_keys(" ".join(str(i) for i in range(20)))
    # browser.find_element_by_css_selector('[name="code"]').send_keys(" ".join(str(i) for i in range(10)))
    Select(browser.find_element_by_css_selector('[name="select-multiple"]')).select_by_index(0)
    # browser. find_element_by_css_selector('[name="select"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="checkbox-inline"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="checkbox"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="radio-inline"]'). send_keys("name")
    # browser. find_element_by_css_selector('[name="radio"]'). send_keys("name")
    browser.find_element_by_css_selector('[name="file_upload"]').send_keys(img_path)

    browser.find_element_by_css_selector('button[value="submit2"]').click()
    time.sleep(0.5)
    percySnapshot(browser=browser, name='input group all invalid')

    browser.find_element_by_css_selector('[name="password"]').clear()
    browser.find_element_by_css_selector('[name="password"]').send_keys("123")
    browser.find_element_by_css_selector('button[value="submit2"]').click()
    time.sleep(0.5)
    percySnapshot(browser=browser, name='input group all submit')


if __name__ == '__main__':
    import util

    util.run_test(start_test_server, test)
