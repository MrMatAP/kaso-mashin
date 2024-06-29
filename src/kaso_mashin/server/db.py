import pathlib
import shutil

from sqlalchemy.orm import Session
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from kaso_mashin import Base
from kaso_mashin.common import EntityModel
from kaso_mashin.common.config import Config


class DB:
    """
    Persistence for kaso_mashin
    """

    def __init__(self, config: Config):
        self._config = config
        self._engine = None
        self._session = None
        self._async_sessionmaker = None
        self._path = pathlib.Path(f"{self._config.path}/kaso.sqlite3")
        self._owning_user = None

    def __del__(self):
        """
        Destructor
        """
        if self._session:
            self._session.close()

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def owning_user(self) -> str:
        return self._owning_user

    @owning_user.setter
    def owning_user(self, value: str):
        self._owning_user = value

    @property
    def engine(self) -> Engine:
        if not self._engine:
            self._engine = create_engine(f"sqlite:///{self.path}")
            Base.metadata.create_all(self._engine)
        return self._engine

    @property
    def session(self) -> Session:
        if not self._session:
            self._session = Session(self.engine)
            shutil.chown(self.path, user=self.owning_user)
        return self._session

    @property
    async def async_sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if not self._async_sessionmaker:
            engine = create_async_engine(f"sqlite+aiosqlite:///{self.path}")
            self._async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
            async with engine.begin() as conn:
                await conn.run_sync(EntityModel.metadata.create_all)
            shutil.chown(self.path, user=self.owning_user)
        return self._async_sessionmaker
