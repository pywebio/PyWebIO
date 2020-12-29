"""
文档中示例代码在线运行
^^^^^^^^^^^^^^^^
"""
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
from os import path, listdir
from functools import partial

here_dir = path.dirname(path.abspath(__file__))


def gen_snippets(code):
    parts = code.split('\n## ----\n')
    for p in parts:
        p = p.replace('\n## ', '\n')
        p = p.replace('\n##\n', '\n\n')

        yield p.lstrip('## ').lstrip('##').strip('\n')


def run_code(code, scope):
    with use_scope(scope):
        exec(code, globals())


def copytoclipboard(code):
    run_js("navigator.clipboard.writeText(text)", text=code)
    toast('已复制')


def handle_code(code, title):
    if title:
        put_markdown('## %s' % title)

    for p in gen_snippets(code):
        with use_scope() as scope:
            put_code(p, 'python')

            put_buttons(['运行', '复制代码'], onclick=[
                partial(run_code, code=p, scope=scope),
                partial(copytoclipboard, code=p)
            ])

        put_markdown('----')

    hold()


def get_app():
    app = {}
    try:
        demos = listdir(path.join(here_dir, 'doc_domes'))
    except:
        demos = []

    demo_infos = []
    for name in demos:
        code = open(path.join(here_dir, 'doc_domes', name)).read()
        title, code = code.split('\n\n', 1)
        app[name] = partial(handle_code, code=code, title=title)
        demo_infos.append([name, title])

    index_html = "<ul>"
    for name, title in demo_infos:
        index_html += '''<li> <a href="javascript:WebIO.openApp('{name}', true)">{name}</a>: {desc} </li>\n'''.format(
            name=name, desc=title)
    index_html += "</ul>"

    def index():
        put_markdown('# PyWebIO Document Code Example Index')
        put_html(index_html)

    app['index'] = index
    return app


if __name__ == '__main__':
    start_server(get_app(), debug=True, port=8080)
