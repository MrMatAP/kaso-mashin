import os
import pathlib
import logging.config
import importlib.metadata
from rich.console import Console
from sqlalchemy.orm import DeclarativeBase

try:
    __version__ = importlib.metadata.version('kaso-mashin')
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = '0.0.0.dev0'

logging.config.dictConfig({
    'version': 1,
    'loggers': {
        '': {'level': 'INFO'},
        'httpx': {'level': 'WARNING'},
        'httpcore': {'level': 'WARNING'}
    },
})
log = logging.getLogger(__name__)
console = Console(log_time=True, log_path=False)

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
