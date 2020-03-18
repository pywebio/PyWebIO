import json

import tornado
import tornado.websocket
from ..framework import WebIOSession


def webio_handler(coro_func, debug=True):
    class WSHandler(tornado.websocket.WebSocketHandler):

        def check_origin(self, origin):
            return True

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        def on_coro_msg(self, controller):
            while controller.unhandled_server_msgs:
                msg = controller.unhandled_server_msgs.pop()
                self.write_message(json.dumps(msg))

        def open(self):
            print("WebSocket opened")
            self.set_nodelay(True)

            self.controller = WebIOSession(coro_func, on_coro_msg=self.on_coro_msg, on_session_close=self.close)

        def on_message(self, message):
            # print('on_message', message)
            data = json.loads(message)
            self.controller.send_client_msg(data)

        def on_close(self):
            self.controller.close(no_session_close_callback=True)
            print("WebSocket closed")

    return WSHandler
