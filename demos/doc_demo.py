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
    code = code.replace('# ..demo-only', '')
    code = '\n'.join(i for i in code.splitlines() if '# ..doc-only' not in i)

    parts = code.split('\n## ----\n')
    for p in parts:
        yield p.strip('\n')


def run_code(code, scope, locals):
    with use_scope(scope):
        try:
            exec(code, globals(), locals)
        except Exception as e:
            toast('代码产生异常："%s:%s"' % (type(e).__name__, e), color='error')


IMPORT_CODE = """from pywebio.input import *
from pywebio.output import *
from pywebio.session import *

"""


def copytoclipboard(code):
    run_js("writeText(text)", text=code)
    toast('已复制')


def handle_code(code, title):
    run_js("""
    window.writeText = function(text) {
        const input = document.createElement('INPUT');
        input.style.opacity  = 0;
        input.style.position = 'absolute';
        input.style.left = '-100000px';
        document.body.appendChild(input);

        input.value = text;
        input.select();
        input.setSelectionRange(0, text.length);
        document.execCommand('copy');
        document.body.removeChild(input);
        return true;
    }
    """)
    locals = {}
    if title:
        put_markdown('## %s' % title)

    for p in gen_snippets(code):
        with use_scope() as scope:
            put_code(p, 'python')

            put_buttons(['运行', '复制代码'], onclick=[
                partial(run_code, code=p, scope=scope, locals=locals),
                partial(copytoclipboard, code=IMPORT_CODE + p)
            ])

        put_markdown('----')

    hold()


def get_app():
    app = {}
    try:
        demos = listdir(path.join(here_dir, 'doc_domes'))
    except Exception:
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
