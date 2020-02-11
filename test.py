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
