import pathlib
import shutil
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.asyncio

from kaso_mashin import Base
from kaso_mashin.common.config import Config

from kaso_mashin.common import EntityModel


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
    def engine(self) -> sqlalchemy.Engine:
        if not self._engine:
            self._engine = sqlalchemy.create_engine(f"sqlite:///{self.path}")
            Base.metadata.create_all(self._engine)
        return self._engine

    @property
    def session(self) -> sqlalchemy.orm.Session:
        if not self._session:
            self._session = sqlalchemy.orm.Session(self.engine)
            shutil.chown(self.path, user=self.owning_user)
        return self._session

    @property
    async def async_sessionmaker(
        self,
    ) -> sqlalchemy.ext.asyncio.async_sessionmaker[sqlalchemy.ext.asyncio.AsyncSession]:
        if not self._async_sessionmaker:
            engine = sqlalchemy.ext.asyncio.create_async_engine(
                f"sqlite+aiosqlite:///{self.path}"
            )
            self._async_sessionmaker = sqlalchemy.ext.asyncio.async_sessionmaker(
                engine, expire_on_commit=False
            )
            async with engine.begin() as conn:
                await conn.run_sync(EntityModel.metadata.create_all)
            shutil.chown(self.path, user=self.owning_user)
        return self._async_sessionmaker
