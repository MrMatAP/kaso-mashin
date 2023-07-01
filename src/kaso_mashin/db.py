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
        self._session = None

    def __del__(self):
        """
        Destructor
        """
        if self._session:
            self._session.close()

    @property
    def config(self) -> Config:
        return self._config

    @property
    def engine(self) -> sqlalchemy.Engine:
        if not self._engine:
            self._engine = sqlalchemy.create_engine(f'sqlite:///{self.config.path}/cloud.sqlite3')
            Base.metadata.create_all(self._engine)
        return self._engine

    @property
    def session(self) -> sqlalchemy.orm.Session:
        if not self._session:
            self._session = sqlalchemy.orm.Session(self.engine)
        return self._session
