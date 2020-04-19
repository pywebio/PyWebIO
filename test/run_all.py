import os
import subprocess
from os import path

here_dir = path.dirname(path.abspath(__file__))


def run_all_test():
    """顺序运行所有测试用例"""
    files = [f for f in os.listdir(here_dir) if path.isfile(f) and f.split('.', 1)[0].isdigit()]
    files.sort(key=lambda f: int(f.split('.', 1)[0]))

    for f in files:
        file = path.join(here_dir, f)
        print("Run test script: %s" % file)
        res = subprocess.run(['python3', file, 'auto'], text=True, shell=True)
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr)


if __name__ == '__main__':
    run_all_test()
