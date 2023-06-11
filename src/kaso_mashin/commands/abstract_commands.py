import abc
import argparse

from kaso_mashin.config import Config
from kaso_mashin.db import DB


class AbstractCommands(abc.ABC):
    """
    An abstract base class for command groups
    """

    def __init__(self, config: Config, db: DB):
        self._config = config
        self._db = db

    @abc.abstractmethod
    def register_commands(self, parser: argparse.ArgumentParser):
        pass

    @property
    def config(self) -> Config:
        return self._config

    @property
    def db(self) -> DB:
        return self._db
