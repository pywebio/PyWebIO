from os.path import abspath, dirname

project_dir = dirname(dirname(abspath(__file__)))

STATIC_PATH = '%s/html' % project_dir

from .tornado import start_server

__all__ = ['start_server']
