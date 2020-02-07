from tornado import gen
from tornado.ioloop import IOLoop
from tornado import websocket
import json


from wsrepl.ioloop import start_ioloop
from wsrepl.interact import *

# 业务逻辑 协程
def say_hello():
    # 向用户输出文字
    text_print("Welcome！！！")
    name = yield from text_input_coro('input your name')
    text_print("Hello %s!" % name)

    age = yield from text_input_coro('input your age')
    if int(age) < 30:
        text_print("Wow. So young!!")
    else:
        text_print("Old man~")



start_ioloop(say_hello)



