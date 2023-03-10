from . import input  # enable `pywebio.input.xxx` expression without `import pywebio.input`
from . import output
from . import platform
from . import session
from . import pin

from .__version__ import __author__, __author_email__, __license__
from .__version__ import __description__, __url__, __version__
from .exceptions import SessionException, SessionClosedException, SessionNotFoundException
from .platform import start_server
from .platform.bokeh import try_install_bokeh_hook
from .platform.page import config
from .utils import STATIC_PATH

try_install_bokeh_hook()
del try_install_bokeh_hook


def enable_debug(level=None):
    """Output PyWebIO logging message to sys.stderr"""
    import logging
    from tornado.log import access_log, app_log, gen_log
    level = level or logging.DEBUG
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('[%(levelname)s %(asctime)s %(module)s:%(lineno)d %(funcName)s] %(message)s',
                                  datefmt='%y%m%d %H:%M:%S')
    ch.setFormatter(formatter)
    for logger in [logging.getLogger(__name__), access_log, app_log, gen_log]:
        logger.handlers = [ch]
        logger.setLevel(level)
        logger.propagate = False
