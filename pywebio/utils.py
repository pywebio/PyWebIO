import random
import socket
import string
from collections import OrderedDict
from contextlib import closing


def get_free_port():
    """
    pick a free port number
    :return int: port number
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def random_str(len=16):
    """生成小写字母和数组组成的随机字符串

    :param int len: 字符串长度
    """
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(len))


def run_as_function(gen):
    res = None
    while 1:
        try:
            res = gen.send(res)
        except StopIteration as e:
            if len(e.args) == 1:
                return e.args[0]
            return


async def to_coroutine(gen):
    res = None
    while 1:
        try:
            c = gen.send(res)
            res = await c
        except StopIteration as e:
            if len(e.args) == 1:
                return e.args[0]
            return



class LRUDict(OrderedDict):
    """
    Store items in the order the keys were last recent updated.

    The last recent updated item was in end.
    The last furthest updated item was in front.
    """

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self.move_to_end(key)
