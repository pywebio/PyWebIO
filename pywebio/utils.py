import random, string


def random_str(len=16):
    """生成小写字母和数组组成的随机字符串

    :param int len: 字符串长度
    """
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(len))
