import tornado.websocket
import time, json
from collections import defaultdict
from .framework import Future, Msg, Global


def run_async(coro):
    Global.active_ws.inactive_coro_instances.append(coro)


def send_msg(cmd, spec):
    msg = dict(command=cmd, spec=spec, coro_id=Global.active_coro_id)
    Global.active_ws.write_message(json.dumps(msg))


def get_response(cmd, spec):
    send_msg(cmd, spec)
    response_msg = yield from Future()
    return response_msg


# 非阻塞协程工具库
def text_input_coro(prompt):
    data = yield from get_response("input_group", spec={
        "label": prompt,
        "inputs": [{
            'name': 'name',
            'type': 'text',
            'label': prompt,
            'help_text': 'help_text',

        }]
    })
    input_text = data['data']
    return input_text['name']


def ctrl_coro(ctrl_info):
    msg = dict(command="ctrl", spec=ctrl_info)
    Global.active_ws.write_message(json.dumps(msg))


def text_print(text, *, ws=None):
    print('text_print', Global.active_ws, text)
    msg = dict(command="output", spec=dict(content=text, type='text'))
    (ws or Global.active_ws).write_message(json.dumps(msg))


def json_print(obj):
    text = "```\n%s\n```" % json.dumps(obj, indent=4, ensure_ascii=False)
    text_print(text)
