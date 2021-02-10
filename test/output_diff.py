import os
import sys


def diff_file(file_a, file_b):
    if open(file_a).read() != open(file_b).read():
        cmd = 'diff %s %s' % (file_a, file_b)
        print('#' * 4, cmd, '#' * 4)
        os.system(cmd)
        return True
    return False


def diff_dir(dir):
    files = [os.path.join(dir, f) for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    has_diff = any(diff_file(files[idx - 1], files[idx]) for idx in range(1, len(files)))
    if has_diff:
        sys.exit(1)


if __name__ == '__main__':
    here_dir = os.path.dirname(os.path.abspath(__file__))
    diff_dir(os.path.join(here_dir, 'output'))
