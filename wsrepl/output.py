import json
import logging
from collections.abc import Mapping

from .framework import Global
from .input_ctrl import send_msg, single_input, input_control


def set_title(title):
    send_msg('output_ctl', dict(title=title))


def text_print(text, *, ws=None):
    msg = dict(command="output", spec=dict(content=text, type='text'))
    (ws or Global.active_ws).write_message(json.dumps(msg))


def json_print(obj):
    text = "```\n%s\n```" % json.dumps(obj, indent=4, ensure_ascii=False)
    text_print(text)


put_markdown = text_print


def put_table(tdata):
    """
    |      \|      |      |      |
    | ---- | ---- | ---- | ---- |
    |      |      |      |      |
    |      |      |      |      |
    |      |      |      |      |
    :param tdata:
    :return:
    """

    def quote(data):
        return data.replace('|', r'\|')

    header = "|%s|" % "|".join(map(quote, tdata[0]))
    res = [header]
    res.append("|%s|" % "|".join(['----'] * len(tdata[0])))
    for tr in tdata[1:]:
        t = "|%s|" % "|".join(map(quote, tr))
        res.append(t)
    text_print('\n'.join(res))


def buttons(buttons, onclick=None):
    pass