from tornado import gen
from tornado.ioloop import IOLoop
from tornado import websocket
import json

from wsrepl.ioloop import start_ioloop
from wsrepl.interact import *
from tornado.gen import sleep


# 业务逻辑 协程
def say_hello():
    # 向用户输出文字
    text_print("Welcome！！！")
    res = yield from select('This is select input', [
        {'value': 1, 'label': 'one', 'selected': False, 'disabled': False},
        {'value': 2, 'label': 'two', 'selected': True, 'disabled': False},
        {'value': 2, 'label': 'three disabled', 'selected': False, 'disabled': True},
    ], type=SELECT, multiple=False)
    text_print('Your input:%s' % res)

    res = yield from select('This is multiple select input', [
        {'value': 1, 'label': 'one', 'selected': True, 'disabled': False},
        {'value': 2, 'label': 'two', 'selected': True, 'disabled': False},
        {'value': 2, 'label': 'three disabled', 'selected': False, 'disabled': True},
    ], type=SELECT, multiple=True)
    text_print('Your input:%s' % res)

    res = yield from select('This is RADIO input', [
        {'value': 1, 'label': 'one', 'selected': False, 'disabled': False},
        {'value': 2, 'label': 'two', 'selected': True, 'disabled': False},
        {'value': 2, 'label': 'three disabled', 'selected': False, 'disabled': True},
    ], type=RADIO, multiple=True)
    text_print('Your input:%s' % res)

    res = yield from select('This is CHECKBOX input', [
        {'value': 1, 'label': 'one', 'selected': False, 'disabled': False},
        {'value': 2, 'label': 'two', 'selected': True, 'disabled': False},
        {'value': 2, 'label': 'three disabled', 'selected': False, 'disabled': True},
    ], type=CHECKBOX, multiple=True)
    text_print('Your input:%s' % res)

    res = yield from input('This is single input')
    text_print('Your input:%s' % res)

    res = yield from input('This is another single input')
    text_print('Your input:%s' % res)

    res = yield from input_group('Group input', [
        input('Input 1', name='one'),
        input('Input 2', name='two'),
        select('Input 2', options=['A', 'B', 'C'], type=CHECKBOX, name='three')
    ])

    text_print('Your input:')
    json_print(res)


start_ioloop(say_hello)
