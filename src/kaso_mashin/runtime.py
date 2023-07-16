import ipaddress

import netifaces

from kaso_mashin.config import Config
from kaso_mashin.db import DB
from kaso_mashin.controllers import (
    BootstrapController, DiskController, IdentityController, ImageController, InstanceController,
    NetworkController, PhoneHomeController, TaskController)
from kaso_mashin.model import NetworkKind, NetworkModel


class Runtime:
    """
    A generic runtime holding objects we intend to exist as singletons
    """

    def __init__(self, config: Config, db: DB):
        self._config = config
        self._db = db
        self._server_url = None
        self._bootstrap_controller = BootstrapController(config=config, db=db)
        self._disk_controller = DiskController(config=config, db=db)
        self._identity_controller = IdentityController(config=config, db=db)
        self._image_controller = ImageController(config=config, db=db)
        self._instance_controller = InstanceController(config=config, db=db)
        self._network_controller = NetworkController(config=config, db=db)
        self._phonehome_controller = PhoneHomeController(config=config, db=db)
        self._task_controller = TaskController(config=config, db=db)

    def late_init(self, server: bool=False):
        """
        Perform late initialisation after configuration
        """
        self._server_url = f'http://{self.config.default_server_host}:{self.config.default_server_port}'
        if not server:
            return
        # TODO: Network updates should only happen in server mode, NOT in client mode
        if not self.network_controller.get(name=NetworkController.DEFAULT_BRIDGED_NETWORK_NAME):
            gateway = netifaces.gateways().get('default')
            host_if = list(gateway.values())[0][1]
            host_addr = netifaces.ifaddresses(host_if)[netifaces.AF_INET][0]
            model = NetworkModel(name=NetworkController.DEFAULT_BRIDGED_NETWORK_NAME,
                                 kind=NetworkKind.VMNET_BRIDGED,
                                 host_phone_home_port=self.config.default_phone_home_port,
                                 host_if=list(gateway.values())[0][1],
                                 host_ip4=host_addr.get('addr'),
                                 nm4=host_addr.get('netmask'),
                                 gw4=list(gateway.values())[0][0])
            self.network_controller.create(model)
        if not self.network_controller.get(name=NetworkController.DEFAULT_HOST_NETWORK_NAME):
            host_net = ipaddress.ip_network(self.config.default_host_network_cidr)
            model = NetworkModel(name=NetworkController.DEFAULT_HOST_NETWORK_NAME,
                                 kind=NetworkKind.VMNET_HOST,
                                 host_phone_home_port=self.config.default_phone_home_port,
                                 host_ip4=host_net.network_address + 1,
                                 nm4=host_net.netmask,
                                 dhcp4_start=host_net.network_address + 10,
                                 dhcp4_end=host_net.broadcast_address - 1)
            self.network_controller.create(model)
        if not self.network_controller.get(name=NetworkController.DEFAULT_SHARED_NETWORK_NAME):
            shared_net = ipaddress.ip_network(self.config.default_shared_network_cidr)
            model = NetworkModel(name=NetworkController.DEFAULT_SHARED_NETWORK_NAME,
                                 kind=NetworkKind.VMNET_SHARED,
                                 host_phone_home_port=self.config.default_phone_home_port,
                                 host_ip4=shared_net.network_address + 1,
                                 nm4=shared_net.netmask,
                                 dhcp4_start=shared_net.network_address + 10,
                                 dhcp4_end=shared_net.broadcast_address - 1)
            self.network_controller.create(model)

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
    def bootstrap_controller(self) -> BootstrapController:
        return self._bootstrap_controller

    @property
    def disk_controller(self) -> DiskController:
        return self._disk_controller

    @property
    def identity_controller(self) -> IdentityController:
        return self._identity_controller

    @property
    def image_controller(self) -> ImageController:
        return self._image_controller

    @property
    def instance_controller(self) -> InstanceController:
        return self._instance_controller

    @property
    def network_controller(self) -> NetworkController:
        return self._network_controller

    @property
    def phonehome_controller(self) -> PhoneHomeController:
        return self._phonehome_controller

    @property
    def task_controller(self) -> TaskController:
        return self._task_controller
