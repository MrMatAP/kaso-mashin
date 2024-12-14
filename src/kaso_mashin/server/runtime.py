import logging
import os
import contextlib

import fastapi
import getpass

from kaso_mashin.services.db_service import DB

from kaso_mashin.domain.instance import InstanceRepository
from kaso_mashin.common.domain.bootstrap import BootstrapRepository
from kaso_mashin.domain.network import NetworkRepository
from kaso_mashin.common.domain.disk import DiskRepository
from kaso_mashin.common.domain.image import ImageRepository
from kaso_mashin.domain.identity import IdentityRepository
from kaso_mashin.common.domain import Bootstrap, Disk, Identity, \
    Image, Instance, Network
from kaso_mashin.common import ConfigService, \
    IdentityModel, ImageModel, DiskModel, \
    NetworkModel, BootstrapModel, InstanceModel
from kaso_mashin.services import QEMUService, EventService, TaskService


class Runtime:
    """
    A generic runtime holding objects we intend to exist as singletons
    """

    def __init__(self, config: ConfigService, db: DB):
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._config = config
        self._db = db
        self._effective_user = getpass.getuser()
        self._owning_user = os.environ.get("SUDO_USER", self._effective_user)
        self._db.owning_user = self._owning_user
        self._task_repository: TaskService | None = None
        self._disk_repository: DiskRepository | None = None
        self._image_repository: ImageRepository | None = None
        self._network_repository: NetworkRepository | None = None
        self._instance_repository: InstanceRepository | None = None
        self._bootstrap_repository: BootstrapRepository | None = None
        self._identity_repository: IdentityRepository | None = None
        self._uefi_code_path = config.bootstrap_path / "uefi-code.fd"
        self._uefi_vars_path = config.bootstrap_path / "uefi-vars.fd"
        self._event_service = EventService(self)
        self._qemu_service = QEMUService(self)



    @contextlib.asynccontextmanager
    async def lifespan(self, app: fastapi.FastAPI):
        del app
        # self._task_repository = TaskService(
        #     runtime=self,
        #     session_maker=await self._db.async_sessionmaker,
        #     aggregate_root_class=TaskEntity,
        #     model_class=TaskModel,
        # )
        self._disk_repository = DiskRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=Disk,
            model_class=DiskModel,
        )
        self._image_repository = ImageRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=Image,
            model_class=ImageModel,
        )
        self._network_repository = NetworkRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=Network,
            model_class=NetworkModel,
        )
        self._instance_repository = InstanceRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=Instance,
            model_class=InstanceModel,
        )
        self._bootstrap_repository = BootstrapRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=Bootstrap,
            model_class=BootstrapModel,
        )
        self._identity_repository = IdentityRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=Identity,
            model_class=IdentityModel,
        )
        await self.lifespan_networks()
        await self.lifespan_uefi()
        await self.lifespan_bootstrap()
        yield

    @property
    def task_repository(self) -> TaskService:
        return self._task_repository

    @property
    def disk_repository(self) -> DiskRepository:
        return self._disk_repository

    @property
    def image_repository(self) -> ImageRepository:
        return self._image_repository

    @property
    def network_repository(self) -> NetworkRepository:
        return self._network_repository

    @property
    def instance_repository(self) -> InstanceRepository:
        return self._instance_repository

    @property
    def bootstrap_repository(self) -> BootstrapRepository:
        return self._bootstrap_repository

    @property
    def identity_repository(self) -> IdentityRepository:
        return self._identity_repository

    @property
    def event_service(self) -> EventService:
        return self._event_service

    @property
    def qemu_service(self) -> QEMUService:
        return self._qemu_service

    @property
    def config(self) -> ConfigService:
        return self._config

    @property
    def db(self) -> DB:
        return self._db

    @property
    def effective_user(self) -> str:
        return self._effective_user

    @property
    def owning_user(self) -> str:
        return self._owning_user

    @property
    def uefi_code_path(self):
        return self._uefi_code_path

    @property
    def uefi_vars_path(self):
        return self._uefi_vars_path