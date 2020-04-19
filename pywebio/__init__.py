from .platform import start_server
from . import input
from . import output
from .session import *
from .exceptions import SessionException, SessionClosedException, SessionNotFoundException
from .utils import STATIC_PATH

from .__version__ import __description__, __url__, __version__
from .__version__ import __author__, __author_email__, __license__, __copyright__

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler, StreamHandler

logging.getLogger(__name__).addHandler(NullHandler())


def enable_debug(level=logging.DEBUG):
    """Output PyWebIO logging message to sys.stderr"""
    ch = StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('[%(levelname)s %(asctime)s %(module)s:%(lineno)d %(funcName)s] %(message)s',
                                  datefmt='%y%m%d %H:%M:%S')
    ch.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.handlers = [ch]
    logger.setLevel(level)
    logger.propagate = False
