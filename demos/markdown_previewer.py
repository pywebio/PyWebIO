"""
Markdown Live Preview
^^^^^^^^^^^^^^^^^^^^^^^^^^
The online markdown editor with live preview.

:demo_host:`Demo </markdown_previewer>`, `Source code <https://github.com/wang0618/PyWebIO/blob/dev/demos/markdown_previewer.py>`_
"""
from pywebio import start_server

from pywebio.output import *
from pywebio.pin import *
from pywebio.session import set_env, download


def main():
    """Markdown Previewer"""
    set_env(output_animation=False)

    put_markdown("""# Markdown Live Preview
    The online markdown editor with live preview. The source code of this application is [here](https://github.com/wang0618/PyWebIO/blob/dev/demos/markdown_previewer.py).
    ## Write your Markdown
    """, lstrip=True)
    put_textarea('md_text', rows=18, code=True)

    put_buttons(['Download content'], lambda _: download('saved.md', pin.md_text.encode('utf8')), small=True)

    put_markdown('## Preview')
    while True:
        change_detail = pin_wait_change('md_text')
        with use_scope('md', clear=True):
            put_markdown(change_detail['value'], sanitize=False)


if __name__ == '__main__':
    start_server(main, port=8080, debug=True, cdn=False)
