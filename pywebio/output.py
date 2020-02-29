import json
import logging
from collections.abc import Mapping
from base64 import b64encode
from .framework import Global, Task
from .input_ctrl import send_msg, single_input, input_control, next_event, run_async
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
    |      \|      |      |      |
    | ---- | ---- | ---- | ---- |
    |      |      |      |      |
    |      |      |      |      |
    |      |      |      |      |
    :param tdata:
    :param header: 列表，当tdata为字典列表时，header指定表头顺序
    :return:
    """
    if header:
        tdata = [
            [row.get(k, '') for k in header]
            for row in tdata
        ]

    def quote(data):
        return data.replace('|', r'\|')

    header = "|%s|" % "|".join(map(quote, tdata[0]))
    res = [header]
    res.append("|%s|" % "|".join(['----'] * len(tdata[0])))
    for tr in tdata[1:]:
        t = "|%s|" % "|".join(map(quote, tr))
        res.append(t)
    text_print('\n'.join(res))


def buttons(buttons, onclick_coro, small=False,save=None, mutex_mode=False):
    """
    :param buttons: button列表， button可用形式：
        {value:, label:, }
        (value, label,)
        value 单值，label等于value
    :param onclick_coro: CallBack(data, save) todo 允许onclick_coro非coro
    :param save:
    :param mutex_mode: 互斥模式，回调在运行过程中，无法响应同一回调
    :return:
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

    async def callback_coro():
        while True:
            event = await next_event()
            assert event['event'] == 'callback'
            coro = None
            if asyncio.iscoroutinefunction(onclick_coro):
                coro = onclick_coro(event['data'], save)
            elif inspect.isgeneratorfunction(onclick_coro):
                coro = asyncio.coroutine(onclick_coro)(save, event['data'])
            else:
                onclick_coro(event['data'], save)

            if coro is not None:
                if mutex_mode:
                    await coro
                else:
                    run_async(coro)

    print('Global.active_ws', Global.active_ws)
    callback = Task(callback_coro(), Global.active_ws)
    callback.coro.send(None)  # 激活，Non't callback.step() ,导致嵌套调用step  todo 与inactive_coro_instances整合
    # callback_id = callback.coro_id
    Global.active_ws.coros[callback.coro_id] = callback

    send_msg('output', dict(type='buttons', callback_id=callback.coro_id, buttons=btns, small=small))


def put_file(name, content):
    """
    :param name: file name
    :param content: bytes-like object
    :return:
    """
    content = b64encode(content).decode('ascii')
    send_msg('output', dict(type='file', name=name, content=content))
