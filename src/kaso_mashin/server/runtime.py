import os
import pathlib
import shutil
import contextlib

import fastapi
import getpass
import httpx
import aiofiles
import ipaddress
import netifaces

from kaso_mashin.common.config import Config
from kaso_mashin.server.db import DB

from kaso_mashin.common.entities import (
    TaskRepository, TaskModel, TaskEntity,
    DiskRepository, DiskModel, DiskEntity,
    ImageRepository, ImageModel, ImageEntity,
    NetworkRepository, NetworkModel, NetworkEntity,
    NetworkKind, DEFAULT_SHARED_NETWORK_NAME, DEFAULT_BRIDGED_NETWORK_NAME, DEFAULT_HOST_NETWORK_NAME,
    InstanceRepository, InstanceModel, InstanceEntity,
    BootstrapRepository, BootstrapModel, BootstrapEntity,
    BootstrapKind, DEFAULT_K8S_MASTER_TEMPLATE_NAME, DEFAULT_K8S_SLAVE_TEMPLATE_NAME,
    IdentityRepository, IdentityModel, IdentityEntity
)


class Runtime:
    """
    A generic runtime holding objects we intend to exist as singletons
    """

    def __init__(self, config: Config, db: DB):
        self._config = config
        self._db = db
        self._effective_user = getpass.getuser()
        self._owning_user = os.environ.get('SUDO_USER', self._effective_user)
        self._db.owning_user = self._owning_user
        self._server_url = None
        self._task_repository = None
        self._disk_repository = None
        self._image_repository = None
        self._network_repository = None
        self._instance_repository = None
        self._bootstrap_repository = None
        self._identity_repository = None
        self._uefi_code_path = config.bootstrap_path / 'uefi-code.fd'
        self._uefi_vars_path = config.bootstrap_path / 'uefi-vars.fd'

    async def lifespan_uefi(self):
        client = httpx.AsyncClient(follow_redirects=True, timeout=60)
        if not self.uefi_code_path.exists():
            async with client.stream('GET', url=self._config.uefi_code_url) as resp, aiofiles.open(self.uefi_code_path, 'wb') as file:
                async for chunk in resp.aiter_bytes(chunk_size=8196):
                    await file.write(chunk)
            shutil.chown(path=self.uefi_code_path, user=self._owning_user)
        if not self.uefi_vars_path.exists():
            async with client.stream('GET', url=self._config.uefi_vars_url) as resp, aiofiles.open(self.uefi_vars_path, 'wb') as file:
                async for chunk in resp.aiter_bytes(chunk_size=8196):
                    await file.write(chunk)
                shutil.chown(path=self.uefi_vars_path, user=self._owning_user)

    async def lifespan_bootstrap(self):
        template_dir = pathlib.Path(__file__).parent.parent / 'common' / 'templates'
        ignition_k8s_master = await self.bootstrap_repository.get_by_name(DEFAULT_K8S_MASTER_TEMPLATE_NAME)
        if ignition_k8s_master is None:
            ignition_k8s_master_template = template_dir / 'ignition_k8s_master.yaml'
            await BootstrapEntity.create(name=DEFAULT_K8S_MASTER_TEMPLATE_NAME,
                                         kind=BootstrapKind.IGNITION,
                                         content=ignition_k8s_master_template.read_text(encoding='utf-8'))
        ignition_k8s_slave = await self.bootstrap_repository.get_by_name(DEFAULT_K8S_SLAVE_TEMPLATE_NAME)
        if ignition_k8s_slave is None:
            ignition_k8s_slave_template = template_dir / 'ignition_k8s_slave.yaml'
            await BootstrapEntity.create(name=DEFAULT_K8S_SLAVE_TEMPLATE_NAME,
                                         kind=BootstrapKind.IGNITION,
                                         content=ignition_k8s_slave_template.read_text(encoding='utf-8'))

    async def lifespan_server(self):
        self._server_url = f'http://{self.config.default_server_host}:{self.config.default_server_port}'

    async def lifespan_paths(self):
        for path in self.config.path, self.config.images_path, self.config.instances_path, self.config.bootstrap_path:
            path.mkdir(parents=True, exist_ok=True)
            shutil.chown(path=path, user=self.owning_user)

    async def lifespan_networks(self):
        host_network = await self.network_repository.get_by_name(DEFAULT_HOST_NETWORK_NAME)
        if not host_network:
            await NetworkEntity.create(name=DEFAULT_HOST_NETWORK_NAME,
                                       kind=NetworkKind.VMNET_HOST,
                                       cidr='10.1.0.0/24',
                                       gateway='10.1.0.1')
        shared_network = await self.network_repository.get_by_name(DEFAULT_SHARED_NETWORK_NAME)
        if not shared_network:
            await NetworkEntity.create(name=DEFAULT_SHARED_NETWORK_NAME,
                                       kind=NetworkKind.VMNET_SHARED,
                                       cidr='10.2.0.0/24',
                                       gateway='10.2.0.1')
        bridged_network = await self.network_repository.get_by_name(DEFAULT_BRIDGED_NETWORK_NAME)
        if not bridged_network:
            await NetworkEntity.create(name=DEFAULT_BRIDGED_NETWORK_NAME,
                                       kind=NetworkKind.VMNET_BRIDGED,
                                       cidr='10.3.0.0/24',
                                       gateway='10.3.0.1')

        # # TODO: Network updates should only happen in server mode, NOT in client mode
        # if not self.network_controller.get(name=NetworkController.DEFAULT_BRIDGED_NETWORK_NAME):
        #     gateway = netifaces.gateways().get('default')
        #     host_if = list(gateway.values())[0][1]
        #     host_addr = netifaces.ifaddresses(host_if)[netifaces.AF_INET][0]
        #     model = NetworkModel(name=NetworkController.DEFAULT_BRIDGED_NETWORK_NAME,
        #                          kind=NetworkKind.VMNET_BRIDGED,
        #                          host_phone_home_port=self.config.default_phone_home_port,
        #                          host_if=list(gateway.values())[0][1],
        #                          host_ip4=host_addr.get('addr'),
        #                          nm4=host_addr.get('netmask'),
        #                          gw4=list(gateway.values())[0][0])
        #     self.network_controller.create(model)
        # if not self.network_controller.get(name=NetworkController.DEFAULT_HOST_NETWORK_NAME):
        #     host_net = ipaddress.ip_network(self.config.default_host_network_cidr)
        #     model = NetworkModel(name=NetworkController.DEFAULT_HOST_NETWORK_NAME,
        #                          kind=NetworkKind.VMNET_HOST,
        #                          host_phone_home_port=self.config.default_phone_home_port,
        #                          # vmnet assignes the first dhcp4_start address
        #                          host_ip4=host_net.network_address + 10,
        #                          nm4=host_net.netmask,
        #                          dhcp4_start=host_net.network_address + 10,
        #                          dhcp4_end=host_net.broadcast_address - 1)
        #     self.network_controller.create(model)
        # if not self.network_controller.get(name=NetworkController.DEFAULT_SHARED_NETWORK_NAME):
        #     shared_net = ipaddress.ip_network(self.config.default_shared_network_cidr)
        #     model = NetworkModel(name=NetworkController.DEFAULT_SHARED_NETWORK_NAME,
        #                          kind=NetworkKind.VMNET_SHARED,
        #                          host_phone_home_port=self.config.default_phone_home_port,
        #                          # vmnet assignes the first dhcp4_start address
        #                          host_ip4=shared_net.network_address + 10,
        #                          nm4=shared_net.netmask,
        #                          dhcp4_start=shared_net.network_address + 10,
        #                          dhcp4_end=shared_net.broadcast_address - 1)
        #     self.network_controller.create(model)

    @contextlib.asynccontextmanager
    async def lifespan(self, app: fastapi.FastAPI):
        del app
        self._task_repository = TaskRepository(runtime=self,
                                               session_maker=await self._db.async_sessionmaker,
                                               aggregate_root_class=TaskEntity,
                                               model_class=TaskModel)
        self._disk_repository = DiskRepository(runtime=self,
                                               session_maker=await self._db.async_sessionmaker,
                                               aggregate_root_class=DiskEntity,
                                               model_class=DiskModel)
        self._image_repository = ImageRepository(runtime=self,
                                                 session_maker=await self._db.async_sessionmaker,
                                                 aggregate_root_class=ImageEntity,
                                                 model_class=ImageModel)
        self._network_repository = NetworkRepository(runtime=self,
                                                     session_maker=await self._db.async_sessionmaker,
                                                     aggregate_root_class=NetworkEntity,
                                                     model_class=NetworkModel)
        self._instance_repository = InstanceRepository(runtime=self,
                                                       session_maker=await self._db.async_sessionmaker,
                                                       aggregate_root_class=InstanceEntity,
                                                       model_class=InstanceModel)
        self._bootstrap_repository = BootstrapRepository(runtime=self,
                                                         session_maker=await self._db.async_sessionmaker,
                                                         aggregate_root_class=BootstrapEntity,
                                                         model_class=BootstrapModel)
        self._identity_repository = IdentityRepository(runtime=self,
                                                       session_maker=await self._db.async_sessionmaker,
                                                       aggregate_root_class=IdentityEntity,
                                                       model_class=IdentityModel)
        await self.lifespan_networks()
        await self.lifespan_paths()
        await self.lifespan_server()
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
    def config(self) -> Config:
        return self._config

    @property
    def db(self) -> DB:
        return self._db

    @property
    def server_url(self) -> str:
        return self._server_url

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
