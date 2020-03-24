# version is a human-readable version number.

# version_info is a four-tuple for programmatic comparison. The first
# three numbers are the components of the version number.  The fourth
# is zero for an official release, positive for a development branch,
# or negative for a release candidate or beta (after the base version
# number has been incremented)
version = "0.1.0"
version_info = (0, 1, 0, 0)

from .platform import start_server
from . import input
from . import output
from .session import (
    set_session_implement, run_async, run_asyncio_coroutine, register_thread,
    ThreadBasedWebIOSession, AsyncBasedSession
)
from .exceptions import SessionException, SessionClosedException, SessionNotFoundException
from .utils import STATIC_PATH

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
