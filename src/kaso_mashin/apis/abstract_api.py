import abc
import logging
import fastapi

from kaso_mashin.runtime import Runtime
from kaso_mashin.controllers import (
    BootstrapController, OsDiskController, IdentityController, ImageController, InstanceController,
    NetworkController, PhoneHomeController, TaskController)


class AbstractAPI(abc.ABC):
    """
    An abstract base class for APIs
    """

    def __init__(self, runtime: Runtime):
        self._runtime = runtime
        self._router = None
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.debug('Started')

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def router(self) -> fastapi.APIRouter:
        return self._router

    @property
    def bootstrap_controller(self) -> BootstrapController:
        return self._runtime.bootstrap_controller

    @property
    def disk_controller(self) -> OsDiskController:
        return self._runtime.os_disk_controller

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

    @property
    def task_controller(self) -> TaskController:
        return self._runtime.task_controller
