import contextlib
import sqlalchemy
import sqlalchemy.orm

from kaso_mashin import Base
from kaso_mashin.config import Config


class DB:
    """
    Persistence for kaso_mashin
    """

    def __init__(self, config: Config):
        self._config = config
        self._engine = None

    @contextlib.contextmanager
    def session(self) -> sqlalchemy.orm.Session:
        with sqlalchemy.orm.Session(self.engine, expire_on_commit=False) as s:
            yield s

    @property
    def config(self) -> Config:
        return self._config

    @property
    def engine(self) -> sqlalchemy.Engine:
        if not self._engine:
            self._engine = sqlalchemy.create_engine(f'sqlite:///{self.config.path}/cloud.sqlite3')
            Base.metadata.create_all(self._engine)
        return self._engine
