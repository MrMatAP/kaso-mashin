import os
import pathlib
import logging.config
import importlib.metadata

import rich.logging
from sqlalchemy.orm import DeclarativeBase

try:
    __version__ = importlib.metadata.version("kaso-mashin")
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = "0.0.0.dev0"

console = rich.console.Console(log_time=False, log_path=False)
__log_config__ = {
    "version": 1,
    "formatters": {
        "server": {"format": "[%(name)s] %(message)s"},
        "client": {"format": "[%(name)s] %(message)s"},
    },
    "handlers": {
        "server": {
            "()": "rich.logging.RichHandler",
            "show_time": True,
            "show_path": False,
            "formatter": "server",
        },
        "cui": {
            "()": "rich.logging.RichHandler",
            "show_time": False,
            "show_path": False,
            "formatter": "client",
        },
    },
    "loggers": {
        "": {"level": "INFO", "handlers": ["server"], "propagate": False},
        "kaso_mashin": {"level": "INFO", "handlers": ["server"], "propagate": False},
        "kaso_mashin.cui": {"level": "INFO", "handlers": ["cui"], "propagate": False},
        "httpx": {"level": "WARNING", "handlers": ["server"]},
        "httpcore": {"level": "WARNING", "handlers": ["server"]},
        "uvicorn": {"level": "WARNING", "handlers": ["server"]},
    },
}
logging.config.dictConfig(__log_config__)
log = logging.getLogger(__name__)

default_config_file = pathlib.Path(
    os.environ.get("KASO_MASHIN_CONFIG", "~/.kaso")
).expanduser()


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """
    Base class for database persistence
    """


class KasoMashinException(Exception):
    """
    A dedicated exception for mrmat-playground
    """

    def __init__(
        self, status: int = 500, msg: str = "An unknown exception occurred", task=None
    ):
        super().__init__(msg)
        self._status = status
        self._msg = msg
        if task:
            self._task = task
            self._task.state = "failed"
            self._task.msg = msg

    @property
    def status(self) -> int:
        return self._status

    @property
    def msg(self) -> str:
        return self._msg

    @property
    def task(self):
        return self._task

    def __str__(self) -> str:
        return f"[{self._status}] {self._msg}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self._status}, msg={self._msg})"
