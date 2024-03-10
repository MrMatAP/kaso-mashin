import contextlib
import fastapi
import shutil
import getpass
import os
import ipaddress

import netifaces

from kaso_mashin.common.config import Config
from kaso_mashin.server.db import DB
# from kaso_mashin.server.controllers import (
#     BootstrapController, OsDiskController, IdentityController,
#     InstanceController,
#     NetworkController, PhoneHomeController)
# from kaso_mashin.common.model import NetworkKind, NetworkModel

from kaso_mashin.common.entities import (
    TaskRepository, TaskModel, TaskEntity,
    DiskRepository, DiskModel, DiskEntity,
    ImageRepository, ImageModel, ImageEntity
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
        # self._bootstrap_controller = BootstrapController(runtime=self)
        # self._os_disk_controller = OsDiskController(runtime=self)
        # self._identity_controller = IdentityController(runtime=self)
        # self._instance_controller = InstanceController(runtime=self)
        # self._network_controller = NetworkController(runtime=self)
        # self._phonehome_controller = PhoneHomeController(runtime=self)
        self._task_repository = None
        self._disk_repository = None
        self._image_repository = None

    def late_init(self, server: bool = False):
        """
        Perform late initialisation after configuration
        """
        shutil.chown(self.config.path, user=self.owning_user)
        self._server_url = f'http://{self.config.default_server_host}:{self.config.default_server_port}'
        if not server:
            return
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
        self._task_repository = TaskRepository(session_maker=await self._db.async_sessionmaker,
                                               aggregate_root_class=TaskEntity,
                                               model_class=TaskModel)
        self._disk_repository = DiskRepository(session_maker=await self._db.async_sessionmaker,
                                               aggregate_root_class=DiskEntity,
                                               model_class=DiskModel)
        self._image_repository = ImageRepository(session_maker=await self._db.async_sessionmaker,
                                                 aggregate_root_class=ImageEntity,
                                                 model_class=ImageModel)
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

    # @property
    # def bootstrap_controller(self) -> BootstrapController:
    #     return self._bootstrap_controller
    #
    # @property
    # def os_disk_controller(self) -> OsDiskController:
    #     return self._os_disk_controller
    #
    # @property
    # def identity_controller(self) -> IdentityController:
    #     return self._identity_controller
    #
    # @property
    # def instance_controller(self) -> InstanceController:
    #     return self._instance_controller
    #
    # @property
    # def network_controller(self) -> NetworkController:
    #     return self._network_controller
    #
    # @property
    # def phonehome_controller(self) -> PhoneHomeController:
    #     return self._phonehome_controller
