import argparse
from os import path

from pywebio.platform import path_deploy

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=8080, help="run on the given port", type=int)
    args = parser.parse_args()

    here_dir = path.dirname(path.abspath(__file__))
    path_deploy(here_dir, port=args.port)
