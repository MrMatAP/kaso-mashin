import abc
import argparse

from kaso_mashin.config import Config
from kaso_mashin.db import DB
from kaso_mashin.runtime import Runtime
from kaso_mashin.controllers import (
    BootstrapController, DiskController, IdentityController, ImageController, InstanceController,
    NetworkController, PhoneHomeController)


class AbstractCommands(abc.ABC):
    """
    An abstract base class for command groups
    """

    def __init__(self, runtime: Runtime):
        self._runtime = runtime

    @abc.abstractmethod
    def register_commands(self, parser: argparse.ArgumentParser):
        pass

    @property
    def config(self) -> Config:
        return self._runtime.config

    @property
    def db(self) -> DB:
        return self._runtime.db

    @property
    def bootstrap_controller(self) -> BootstrapController:
        return self._runtime.bootstrap_controller

    @property
    def disk_controller(self) -> DiskController:
        return self._runtime.disk_controller

    @property
    def identity_controller(self) -> IdentityController:
        return self._runtime.identity_controller

    @property
    def image_controller(self) -> ImageController:
        return self._runtime.image_controller

    @property
    def instance_controller(self) -> InstanceController:
        return self._runtime.instance_controller

    @property
    def network_controller(self) -> NetworkController:
        return self._runtime.network_controller

    @property
    def phonehome_controller(self) -> PhoneHomeController:
        return self._runtime.phonehome_controller
