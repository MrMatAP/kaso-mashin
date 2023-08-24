import os
import pathlib
import logging.config
import importlib.metadata

import rich.logging
from sqlalchemy.orm import DeclarativeBase

try:
    __version__ = importlib.metadata.version('kaso-mashin')
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = '0.0.0.dev0'

console = rich.console.Console(log_time=False, log_path=False)
__log_config__ = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '[%(name)s] %(message)s'
        }
    },
    'handlers': {
        'rich': {
            '()': 'rich.logging.RichHandler',
            'show_time': False,
            'show_path': True,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {'level': 'INFO', 'handlers': ['rich'], 'propagate': False},
        'kaso_mashin': {'level': 'INFO', 'handlers': ['rich'], 'propagate': False},
        'httpx': {'level': 'WARNING', 'handlers': ['rich']},
        'httpcore': {'level': 'WARNING', 'handlers': ['rich']},
        'uvicorn': {'level': 'WARNING', 'handlers': ['rich']}
    },
}
logging.config.dictConfig(__log_config__)
log = logging.getLogger(__name__)

default_config_file = pathlib.Path(os.environ.get('KASO_MASHIN_CONFIG', '~/.kaso')).expanduser()


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """
    Base class for database persistence
    """


class KasoMashinException(Exception):
    """
    A dedicated exception for mrmat-playground
    """

    def __init__(self,
                 status: int = 500,
                 msg: str = 'An unknown exception occurred',
                 task=None):
        self.status = status
        self.msg = msg
        if task:
            self.task = task
            task.state = 'failed'
            task.msg = msg

    def __repr__(self):
        return f'PlaygroundException(status={self.status}, msg="{self.msg}")'

    def __str__(self):
        return self.__repr__()
