import tornado.websocket
import time, json
from collections import defaultdict
from .framework import Future, Msg, Global


def _get_response(cmd, spec):

    msg = dict(command=cmd, spec=spec)
    Global.active_ws.write_message(json.dumps(msg))

    response_msg = yield from Future()

    return response_msg


# 非阻塞协程工具库
def text_input_coro(prompt):
    data = yield from _get_response("text_input", spec=dict(prompt=prompt))
    input_text = data['data']
    return input_text


def ctrl_coro(ctrl_info):
    msg = dict(command="ctrl", spec=ctrl_info)
    Global.active_ws.write_message(json.dumps(msg))


def text_print(text, *, ws=None):
    msg = dict(command="text_print", spec=dict(content=text))
    (ws or Global.active_ws).write_message(json.dumps(msg))
