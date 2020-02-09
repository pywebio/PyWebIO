from tornado import gen
from tornado.ioloop import IOLoop
from tornado import websocket
import json

from wsrepl.ioloop import start_ioloop
from wsrepl.interact import *
from tornado.gen import sleep


def other():
    text_print("Welcome from other！！！")


    event = yield from get_response("input_group", spec={
        "label": 'other',
        "inputs": [{
            'name': 'other',
            'type': 'text',
            'autofocus': True,
            'label': 'other',
            'help_text': 'other help_text',
        }]
    })
    idx = 0
    while 1:
        yield sleep(0.5)
        text_print(str(idx))


# 业务逻辑 协程
def say_hello():
    # yield sleep(0.5)

    # 向用户输出文字
    text_print("Welcome！！！")
    # run_async(other())
    # name = yield from text_input_coro('input your name')

    event = yield from get_response("input_group", spec={
        "label": 'another',
        "inputs": [{
            'name': 'name',
            'type': 'text',
            'autofocus': True,
            'label': 'another text',
            'help_text': 'another text help_text',
        }]
    })

    event = yield from get_response("input_group", spec={
        "label": 'label',
        "inputs": [{
            'name': 'name',
            'type': 'text',
            'autofocus': True,
            'label': 'text',
            'help_text': 'text help_text',
        },
            {
                'name': 'checkbox',
                'type': 'checkbox',
                'inline': True,
                'label': '性别',
                'help_text': 'help_text',
                'options': [
                    {'value': 'man', 'label': '男', 'checked': True},
                    {'value': 'woman', 'label': '女', 'checked': False}
                ]
            }
        ]
    })
    json_print(event)

    while event['event'] != 'from_submit':
        json_print(event)
        if event['event'] == 'input_event':
            send_msg("update_input", spec={
                'target_name': event['data']['name'],
                'attributes': {
                    'valid_status': True,
                    'valid_feedback': 'ok'
                }
            })
        event = yield

    yield sleep(0.5)

    text_print("收到")

    yield from get_response("destroy_form", spec={})

    text_print("Bye ")

    yield sleep(1)


start_ioloop(say_hello)
