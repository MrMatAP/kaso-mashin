import abc
import logging
import typing
import argparse
import httpx
import rich.table
import rich.box

from kaso_mashin import console, tracer
from kaso_mashin.config import Config
from kaso_mashin.db import DB
from kaso_mashin.runtime import Runtime
from kaso_mashin.controllers import (
    BootstrapController, OsDiskController, IdentityController, ImageController, InstanceController,
    NetworkController, PhoneHomeController)
from kaso_mashin.model import ExceptionSchema


class AbstractCommands(abc.ABC):
    """
    An abstract base class for command groups
    """

    def __init__(self, runtime: Runtime):
        self._runtime = runtime
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.debug('Started')

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abc.abstractmethod
    def register_commands(self, parser: argparse.ArgumentParser):
        pass

    def api_client(self,
                   uri: str,
                   body: typing.Dict | typing.List = None,
                   method: str = 'GET',
                   expected_status: typing.List = None,
                   fallback_msg: str = 'Something bad and unknown happened...'):
        if expected_status is None:
            expected_status = [200]
        resp = httpx.request(url=f'{self.server_url}{uri}',
                             method=method,
                             json=body)
        if resp.status_code in expected_status:
            return resp
        table = rich.table.Table(title='ERROR', box=rich.box.ROUNDED, show_header=False)
        table.add_row('[red]Status:', str(resp.status_code))
        try:
            ex = ExceptionSchema.model_validate_json(resp.content)
            table.add_row('[red]Message:', ex.msg)
        except ValueError:
            table.add_row('[red]Message:', fallback_msg)
        console.print(table)
        return None

    @property
    def config(self) -> Config:
        return self._runtime.config

    @property
    def db(self) -> DB:
        return self._runtime.db

    @property
    def server_url(self) -> str:
        return self._runtime.server_url

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
