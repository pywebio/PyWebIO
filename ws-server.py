import tornado.websocket
import time, json
from collections import defaultdict


class Future:
    def __init__(self):
        self.result = None
        self._callbacks = []

    def add_done_callback(self, fn):
        self._callbacks.append(fn)

    def set_result(self, result):
        self.result = result
        for fn in self._callbacks:
            fn(self)

    def __iter__(self):
        yield self
        return self.result


class Task:
    def __init__(self, coro):
        self.coro = coro
        f = Future()
        f.set_result(None)
        self.step(f)

        self.result = None  # 协程的返回值
        self.on_task_finish = None  # 协程完毕的回调函数

    def step(self, future):
        try:
            # send会进入到coro执行, 即fetch, 直到下次yield
            # next_future 为yield返回的对象
            next_future = self.coro.send(future.result)
            next_future.add_done_callback(self.step)
        except StopIteration as e:
            if len(e.args) == 1:
                self.result = e.args[0]
            if self.on_task_finish:
                self.on_task_finish(self.result)
            return


# 非阻塞协程工具库
def text_input_coro(prompt):
    """
    yield出来的为Future对象，每次yield前注册event，event的callback为给该Future对象set-result
    yield的返回值为改Future对象的值
    :return:
    """
    # 注册event
    msg_id = Msg.gen_msg_id()
    msg = dict(command="text_input", data=dict(prompt=prompt, msg_id=msg_id))
    f = Future()
    Msg.add_callback(msg_id, f.set_result)

    Global.active_ws.write_message(json.dumps(msg))

    input_text = yield from f
    Msg.unregister_msg(msg_id)

    return input_text


def text_print(text, *, ws=None):
    msg = dict(command="text_print", data=text)
    (ws or Global.active_ws).write_message(json.dumps(msg))


# 业务逻辑 协程
def my_coro():
    text_print("Welcome to ws-repl")
    name = yield from text_input_coro('input your name:')
    text_print("go go go %s!" % name)

    age = yield from text_input_coro('input your age:')
    text_print("So young!!")


class Msg:
    mid2callback = defaultdict(list)

    @staticmethod
    def gen_msg_id():
        mid = '%s-%s' % (Global.active_ws.sid, int(time.time()))
        return mid

    @classmethod
    def add_callback(cls, msg_id, callback):
        cls.mid2callback[msg_id].append(callback)

    @classmethod
    def get_callbacks(cls, msg_id):
        return cls.mid2callback[msg_id]

    @classmethod
    def get_callbacks(cls, msg_id):
        return cls.mid2callback[msg_id]

    @classmethod
    def unregister_msg(cls, msg_id):
        del cls.mid2callback[msg_id]


class Global:
    active_ws: "EchoWebSocket"


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        print("WebSocket opened")
        self.set_nodelay(True)
        ############
        self.sid = int(time.time())
        self.coro = my_coro()

        Global.active_ws = self
        self.task = Task(self.coro)
        self.task.on_task_finish = self.on_task_finish

    def on_task_finish(self, result):
        text_print('Task finish, return: %s\nBye, bye!!' % result, ws=self)
        self.close()

    def on_message(self, message):
        print('on_message', message)
        # self.write_message(u"You said: " + message)
        # { msg_id: , data: }
        data = json.loads(message)

        Global.active_ws = self
        callbacks = Msg.get_callbacks(data['msg_id'])
        for c in callbacks:
            c(data['data'])

    def on_close(self):
        print("WebSocket closed")


handlers = [(r"/test", EchoWebSocket)]
app = tornado.web.Application(handlers=handlers, debug=True)
http_server = tornado.httpserver.HTTPServer(app)
http_server.listen(8080)
tornado.ioloop.IOLoop.instance().start()
