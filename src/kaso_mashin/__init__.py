"""
Main import entry point for MrMat :: Playground
"""

import os
import pathlib
import logging
import importlib.metadata
from rich.console import Console
from rich.logging import RichHandler
from sqlalchemy.orm import DeclarativeBase

try:
    __version__ = importlib.metadata.version('kaso-mashin')
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = '0.0.0.dev0'

logging.basicConfig(level='INFO', handlers=[RichHandler(rich_tracebacks=True)])
log = logging.getLogger(__name__)
console = Console(log_time=True, log_path=False)

default_config_file = pathlib.Path(os.environ.get('KASO_MASHIN_CONFIG', '~/.kaso')).expanduser()

class Base(DeclarativeBase):
    """
    Base class for database persistence
    """
    pass

class KasoMashinException(Exception):
    """
    A dedicated exception for mrmat-playground
    """

    def __init__(self, status=500, msg='An unknown exception occurred'):
        self.status = status
        self.msg = msg

    def __repr__(self):
        return f'PlaygroundException(status={self.status}, msg={self.msg})'

    def __str__(self):
        return self.__repr__()
