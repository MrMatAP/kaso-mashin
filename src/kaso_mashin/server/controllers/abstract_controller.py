import abc
import logging

from kaso_mashin.common.config import Config
from kaso_mashin.server.db import DB


class AbstractController(abc.ABC):
    """
    Abstract base class for all controllers
    """

    def __init__(self, runtime: 'Runtime'):
        self._runtime = runtime
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.info('Started')

    @property
    def config(self) -> Config:
        return self._runtime.config

    @property
    def db(self) -> DB:
        return self._runtime.db

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def bootstrap_controller(self) -> 'BootstrapController':
        return self._runtime.bootstrap_controller

    @property
    def os_disk_controller(self) -> 'DiskController':
        return self._runtime.os_disk_controller

    @property
    def identity_controller(self) -> 'IdentityController':
        return self._runtime.identity_controller

    @property
    def image_controller(self) -> 'ImageController':
        return self._runtime.image_controller

    @property
    def instance_controller(self) -> 'InstanceController':
        return self._runtime.instance_controller

    @property
    def network_controller(self) -> 'NetworkController':
        return self._runtime.network_controller

    @property
    def phonehome_controller(self) -> 'PhoneHomeController':
        return self._runtime.phonehome_controller
