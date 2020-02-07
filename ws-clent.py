from tornado import gen
from tornado.ioloop import IOLoop
from tornado import websocket
import json


@gen.coroutine
def run():
    url = 'ws://localhost:8080/test'
    conn = yield websocket.websocket_connect(url)
    print('connected!')
    while True:
        msg = yield conn.read_message()
        if msg is None:
            print('Connect closed')
            return

        data = json.loads(msg)
        cmd = data['command']
        if cmd == 'text_print':
            print(data['spec']['content'])
        elif cmd == 'text_input':
            input_text = input(data['spec']['prompt'])
            resp = dict(msg_id=data['spec']['msg_id'], data=input_text)
            yield conn.write_message(json.dumps(resp))


IOLoop.current().run_sync(run)
