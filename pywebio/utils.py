import random
import string
from collections import OrderedDict


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
