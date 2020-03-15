import json

import tornado
import tornado.websocket
from .. import project_dir
from ..framework import WebIOSession

STATIC_PATH = '%s/html' % project_dir


def ws_handler(coro_func, debug=True):
    class WSHandler(tornado.websocket.WebSocketHandler):

        def check_origin(self, origin):
            return True

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        def on_server_msg(self, controller):
            while controller.unhandled_server_msgs:
                msg = controller.unhandled_server_msgs.pop()
                self.write_message(json.dumps(msg))

        def open(self):
            print("WebSocket opened")
            self.set_nodelay(True)

            self.controller = WebIOSession(coro_func, server_msg_listener=self.on_server_msg)

        def on_message(self, message):
            # print('on_message', message)
            data = json.loads(message)
            self.controller.add_client_msg(data)

        def on_close(self):
            self.controller.close()
            print("WebSocket closed")

    return WSHandler
