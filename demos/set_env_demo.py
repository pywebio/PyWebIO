"""
`pywebio.session.set_env()` demo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
import datetime
import asyncio


def t(eng, chinese):
    """return English or Chinese text according to the user's browser language"""
    return chinese if 'zh' in info.user_language else eng


async def main():
    """`pywebio.session.set_env()` demo"""

    set_scope('time')
    put_markdown(t('> Can be used to observe the animation effect of the `output_animation` setting',
                   '> 可用于观察 `output_animation` 项的动画效果'))
    put_markdown('---')

    async def bg_task():
        while 1:
            with use_scope('time', clear=True):
                put_text('Current time:', datetime.datetime.now())

            await asyncio.sleep(1)

    run_async(bg_task())

    put_buttons([t('Output some texts', '输出文本')], [lambda: put_text(datetime.datetime.now())])
    put_markdown(t('> Can be used to observe the automatic scrolling effect of the `auto_scroll_bottom` setting',
                   '> 可用于观察 `auto_scroll_bottom` 项的自动滚动效果'))
    put_markdown('---')
    put_text('Some text.\n' * 10)

    state = {
        'title': 'PyWebIO set_env() Demo',
        'output_animation': True,
        'auto_scroll_bottom': False,
    }
    set_env(**state)

    while 1:
        curr_state_info = ', '.join('%s=%r' % (k, v) for k, v in state.items())
        key = await actions(t('Select the setting item to be changed', '选择要更改的会话环境设置项'), list(state.keys()), help_text='Current state: ' + curr_state_info)
        if key == 'title':
            state['title'] = await input('Title', value=state['title'])
            set_env(title=state['title'])
            toast('Title is set to %r' % state['title'])
        elif key in state:
            state[key] = not (state[key])
            set_env(**{key: state[key]})
            toast('`%s` is set to %r' % (key, state[key]))


if __name__ == '__main__':
    start_server(main, debug=True, port=8080, cdn=False)
