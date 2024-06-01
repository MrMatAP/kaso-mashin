import ipaddress
import logging
import os
import pathlib
import shutil
import contextlib
from ipaddress import IPv4Network

import fastapi
import getpass
import httpx
import aiofiles

from kaso_mashin.common.config import Config
from kaso_mashin.server.db import DB

from kaso_mashin.common.entities import (
    TaskRepository,
    TaskModel,
    TaskEntity,
    DiskRepository,
    DiskModel,
    DiskEntity,
    ImageRepository,
    ImageModel,
    ImageEntity,
    NetworkRepository,
    NetworkModel,
    NetworkEntity,
    NetworkKind,
    DEFAULT_SHARED_NETWORK_NAME,
    DEFAULT_BRIDGED_NETWORK_NAME,
    DEFAULT_HOST_NETWORK_NAME,
    InstanceRepository,
    InstanceModel,
    InstanceEntity,
    BootstrapRepository,
    BootstrapModel,
    BootstrapEntity,
    BootstrapKind,
    DEFAULT_K8S_MASTER_TEMPLATE_NAME,
    DEFAULT_K8S_SLAVE_TEMPLATE_NAME,
    IdentityRepository,
    IdentityModel,
    IdentityEntity,
)
from kaso_mashin.common.services import QEMUService, MessagingService


class Runtime:
    """
    A generic runtime holding objects we intend to exist as singletons
    """

    def __init__(self, config: Config, db: DB):
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._config = config
        self._db = db
        self._effective_user = getpass.getuser()
        self._owning_user = os.environ.get("SUDO_USER", self._effective_user)
        self._db.owning_user = self._owning_user
        self._task_repository: TaskRepository | None = None
        self._disk_repository: DiskRepository | None = None
        self._image_repository: ImageRepository | None = None
        self._network_repository: NetworkRepository | None = None
        self._instance_repository: InstanceRepository | None = None
        self._bootstrap_repository: BootstrapRepository | None = None
        self._identity_repository: IdentityRepository | None = None
        self._uefi_code_path = config.bootstrap_path / "uefi-code.fd"
        self._uefi_vars_path = config.bootstrap_path / "uefi-vars.fd"
        self._queue_service = MessagingService(self)
        self._qemu_service = QEMUService(self)

    async def lifespan_uefi(self):
        self._logger.info(f"Lifespan UEFI started")
        client = httpx.AsyncClient(follow_redirects=True, timeout=60)
        if not self.uefi_code_path.exists():
            async with (
                client.stream("GET", url=self._config.uefi_code_url) as resp,
                aiofiles.open(self.uefi_code_path, "wb") as file,
            ):
                async for chunk in resp.aiter_bytes(chunk_size=8196):
                    await file.write(chunk)
            shutil.chown(path=self.uefi_code_path, user=self._owning_user)
        if not self.uefi_vars_path.exists():
            async with (
                client.stream("GET", url=self._config.uefi_vars_url) as resp,
                aiofiles.open(self.uefi_vars_path, "wb") as file,
            ):
                async for chunk in resp.aiter_bytes(chunk_size=8196):
                    await file.write(chunk)
                shutil.chown(path=self.uefi_vars_path, user=self._owning_user)

    async def lifespan_bootstrap(self):
        self._logger.info(f"Lifespan Bootstrap started")
        template_dir = pathlib.Path(__file__).parent.parent / "common" / "templates"
        ignition_k8s_master = await self.bootstrap_repository.get_by_name(
            DEFAULT_K8S_MASTER_TEMPLATE_NAME
        )
        if ignition_k8s_master is None:
            ignition_k8s_master_template = template_dir / "ignition_k8s_master.yaml"
            await BootstrapEntity.create(
                name=DEFAULT_K8S_MASTER_TEMPLATE_NAME,
                kind=BootstrapKind.IGNITION,
                content=ignition_k8s_master_template.read_text(encoding="utf-8"),
            )
        ignition_k8s_slave = await self.bootstrap_repository.get_by_name(
            DEFAULT_K8S_SLAVE_TEMPLATE_NAME
        )
        if ignition_k8s_slave is None:
            ignition_k8s_slave_template = template_dir / "ignition_k8s_slave.yaml"
            await BootstrapEntity.create(
                name=DEFAULT_K8S_SLAVE_TEMPLATE_NAME,
                kind=BootstrapKind.IGNITION,
                content=ignition_k8s_slave_template.read_text(encoding="utf-8"),
            )

    async def lifespan_paths(self):
        self._logger.info(f"Lifespan Paths started")
        for path in (
            self.config.path,
            self.config.images_path,
            self.config.instances_path,
            self.config.bootstrap_path,
        ):
            path.mkdir(parents=True, exist_ok=True)
            shutil.chown(path=path, user=self.owning_user)

    async def lifespan_networks(self):
        self._logger.info(f"Lifespan Networks started")
        host_network = await self.network_repository.get_by_name(DEFAULT_HOST_NETWORK_NAME)
        if not host_network:
            await NetworkEntity.create(
                name=DEFAULT_HOST_NETWORK_NAME,
                kind=NetworkKind.VMNET_HOST,
                cidr=IPv4Network("10.1.0.0/24"),
                gateway=ipaddress.IPv4Address("10.1.0.1"),
            )
        shared_network = await self.network_repository.get_by_name(DEFAULT_SHARED_NETWORK_NAME)
        if not shared_network:
            await NetworkEntity.create(
                name=DEFAULT_SHARED_NETWORK_NAME,
                kind=NetworkKind.VMNET_SHARED,
                cidr=ipaddress.IPv4Network("10.2.0.0/24"),
                gateway=ipaddress.IPv4Address("10.2.0.1"),
            )
        bridged_network = await self.network_repository.get_by_name(DEFAULT_BRIDGED_NETWORK_NAME)
        if not bridged_network:
            await NetworkEntity.create(
                name=DEFAULT_BRIDGED_NETWORK_NAME,
                kind=NetworkKind.VMNET_BRIDGED,
                cidr=ipaddress.IPv4Network("10.3.0.0/24"),
                gateway=ipaddress.IPv4Address("10.3.0.1"),
            )

    @contextlib.asynccontextmanager
    async def lifespan(self, app: fastapi.FastAPI):
        del app
        await self.lifespan_paths()
        self._task_repository = TaskRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=TaskEntity,
            model_class=TaskModel,
        )
        self._disk_repository = DiskRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=DiskEntity,
            model_class=DiskModel,
        )
        self._image_repository = ImageRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=ImageEntity,
            model_class=ImageModel,
        )
        self._network_repository = NetworkRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=NetworkEntity,
            model_class=NetworkModel,
        )
        self._instance_repository = InstanceRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=InstanceEntity,
            model_class=InstanceModel,
        )
        self._bootstrap_repository = BootstrapRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=BootstrapEntity,
            model_class=BootstrapModel,
        )
        self._identity_repository = IdentityRepository(
            runtime=self,
            session_maker=await self._db.async_sessionmaker,
            aggregate_root_class=IdentityEntity,
            model_class=IdentityModel,
        )
        await self.lifespan_networks()
        await self.lifespan_uefi()
        await self.lifespan_bootstrap()
        yield

    @property
    def task_repository(self) -> TaskRepository:
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
    def queue_service(self) -> MessagingService:
        return self._queue_service

    @property
    def qemu_service(self) -> QEMUService:
        return self._qemu_service

    @property
    def config(self) -> Config:
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
