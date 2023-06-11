import abc

from kaso_mashin.config import Config
from kaso_mashin.db import DB


class AbstractController(abc.ABC):
    """
    Abstract base class for all controllers
    """

    def __init__(self, config: Config, db: DB):
        self._config = config
        self._db = db

    @property
    def config(self) -> Config:
        return self._config

    @property
    def db(self) -> DB:
        return self._db
