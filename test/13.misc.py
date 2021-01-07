import asyncio
import subprocess
from functools import partial

from percy import percySnapshot
from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio import start_server
from pywebio.output import *
from pywebio.session import *
from pywebio.utils import *


def target():
    # test session data
    g = data()
    assert g.none is None
    g.one = 1
    g.one += 1
    assert g.one == 2

    # test pywebio.utils
    async def corofunc(**kwargs):
        pass

    def genfunc(**kwargs):
        yield

    corofunc = partial(corofunc, a=1)
    genfunc = partial(genfunc, a=1)

    assert isgeneratorfunction(genfunc)
    assert iscoroutinefunction(corofunc)
    assert get_function_name(corofunc) == 'corofunc'

    get_free_port()

    try:
        yield put_buttons([{'label': 'must not be shown'}], onclick=[lambda: None])
    except Exception:
        pass

    # test deprecated api
    put_table([
        ['Idx', 'Actions'],
        ['1', table_cell_buttons(['edit', 'delete'], onclick=lambda _: None)],
    ])

    popup('title', 'text content')

    @popup('Popup title')
    def show_popup():
        put_html('<h3>Popup Content</h3>')
        put_text('html: <br/>')

    with popup('Popup title') as s:
        put_html('<h3>Popup Content</h3>')
        clear(s)
        put_buttons(['clear()'], onclick=lambda _: clear(s))
    popup('title2', 'text content')
    close_popup()

    with use_scope() as name:
        put_text('no show')
    remove(name)

    with use_scope('test') as name:
        put_text('current scope name:%s' % name)

    with use_scope('test', clear=True):
        put_text('clear previous scope content')

    @use_scope('test')
    def scoped_func(text):
        put_text(text)

    scoped_func('text1 from `scoped_func`')
    scoped_func('text2 from `scoped_func`')

    try:
        put_column([put_text('A'), 'error'])
    except Exception:
        pass

    toast('Awesome PyWebIO!!', duration=0)

    def show_msg():
        put_text("Toast clicked")

    toast('You have new messages', duration=0, onclick=show_msg)

    run_js("$('.toastify').eq(0).click()")

    assert get_scope() == 'ROOT'

    with use_scope('go_app'):
        put_buttons(['Go thread App'], [lambda: go_app('thread', new_window=False)])

    yield hold()


async def corobased():
    await wait_host_port(port=8080, host='127.0.0.1')
    await to_coroutine(target())


def threadbased():
    run_as_function(target())


def test(server_proc: subprocess.Popen, browser: Chrome):
    time.sleep(2)
    percySnapshot(browser=browser, name='misc output')

    coro_out = template.save_output(browser)[-1]

    # browser.get('http://localhost:8080/?app=thread')
    browser.execute_script("arguments[0].click();", browser.find_element_by_css_selector('#pywebio-scope-go_app button'))
    time.sleep(2)

    thread_out = template.save_output(browser)[-1]

    assert coro_out == thread_out


def start_test_server():
    pywebio.enable_debug()
    start_server({'coro': corobased, 'thread': threadbased}, port=8080, host='127.0.0.1', debug=True)


if __name__ == '__main__':
    util.run_test(start_test_server, test, address='http://localhost:8080/?app=coro')
