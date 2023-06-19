import abc
import argparse

from kaso_mashin.config import Config
from kaso_mashin.db import DB
from kaso_mashin.controllers import (
    BootstrapController, DiskController, IdentityController, ImageController, InstanceController,
    NetworkController, PhoneHomeController )

class AbstractCommands(abc.ABC):
    """
    An abstract base class for command groups
    """

    def __init__(self, config: Config, db: DB):
        self._config = config
        self._db = db
        self._bootstrap_controller = BootstrapController(config=config, db=db)
        self._disk_controller = DiskController(config=config, db=db)
        self._identity_controller = IdentityController(config=config, db=db)
        self._image_controller = ImageController(config=config, db=db)
        self._instance_controller = InstanceController(config=config, db=db)
        self._network_controller = NetworkController(config=config, db=db)
        self._phonehome_controller = PhoneHomeController(config=config, db=db)

    @abc.abstractmethod
    def register_commands(self, parser: argparse.ArgumentParser):
        pass

    @property
    def config(self) -> Config:
        return self._config

    @property
    def db(self) -> DB:
        return self._db

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
