import json
import logging
from collections.abc import Mapping
from base64 import b64encode
from .framework import Global, Task
from .input_ctrl import send_msg, single_input, input_control, next_event, run_async
from .output_ctl import register_callback
import asyncio
import inspect


def set_title(title):
    send_msg('output_ctl', dict(title=title))


def text_print(text, *, ws=None):
    if text is None:
        text = ''
    msg = dict(command="output", spec=dict(content=text, type='text'))
    (ws or Global.active_ws).write_message(json.dumps(msg))


def json_print(obj):
    text = "```\n%s\n```" % json.dumps(obj, indent=4, ensure_ascii=False)
    text_print(text)


put_markdown = text_print


def put_table(tdata, header=None):
    """
    输出表格
    :param tdata: list of list|dict
    :param header: 列表，当tdata为字典列表时，header指定表头顺序
    :return:
    """
    if header:
        tdata = [
            [row.get(k, '') for k in header]
            for row in tdata
        ]

    def quote(data):
        return str(data).replace('|', r'\|')

    # 防止当tdata只有一行时，无法显示表格
    if len(tdata) == 1:
        tdata[0:0] = [' '] * len(tdata[0])

    header = "|%s|" % "|".join(map(quote, tdata[0]))
    res = [header]
    res.append("|%s|" % "|".join(['----'] * len(tdata[0])))
    for tr in tdata[1:]:
        t = "|%s|" % "|".join(map(quote, tr))
        res.append(t)
    text_print('\n'.join(res))


def _format_button(buttons):
    """
    格式化按钮参数
    :param buttons: button列表， button可用形式：
        {value:, label:, }
        (value, label,)
        value 单值，label等于value

    :return: [{value:, label:, }, ...]
    """

    btns = []
    for btn in buttons:
        if isinstance(btn, Mapping):
            assert 'value' in btn and 'label' in btn, 'actions item must have value and label key'
        elif isinstance(btn, list):
            assert len(btn) == 2, 'actions item format error'
            btn = dict(zip(('value', 'label'), btn))
        else:
            btn = dict(value=btn, label=btn)
        btns.append(btn)
    return btns


def td_buttons(buttons, onclick, save=None, mutex_mode=False):
    """
    在表格中显示一组按钮
    参数含义同 buttons 函数
    :return:
    """
    btns = _format_button(buttons)
    callback_id = register_callback(onclick, save, mutex_mode)
    tpl = '<button type="button" value="{value}" class="btn btn-primary btn-sm" ' \
          'onclick="WebIO.DisplayAreaButtonOnClick(this, \'%s\')">{label}</button>' % callback_id
    btns_html = [tpl.format(**b) for b in btns]
    return ' '.join(btns_html)


def buttons(buttons, onclick, small=False, save=None, mutex_mode=False):
    """
    显示一组按钮
    :param buttons: button列表， button可用形式：
        {value:, label:, }
        (value, label,)
        value 单值，label等于value
    :param onclick: CallBack(btn_value, save) CallBack can be generator function or coroutine function
    :param save:
    :param mutex_mode: 互斥模式，回调在运行过程中，无法响应同一回调，仅当onclick为协程函数时有效
    :return:
    """
    btns = _format_button(buttons)
    callback_id = register_callback(onclick, save, mutex_mode)
    send_msg('output', dict(type='buttons', callback_id=callback_id, buttons=btns, small=small))


def put_file(name, content):
    """
    :param name: file name
    :param content: bytes-like object
    :return:
    """
    content = b64encode(content).decode('ascii')
    send_msg('output', dict(type='file', name=name, content=content))
