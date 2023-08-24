import abc
import logging
import typing
import argparse
import httpx
import rich.table
import rich.box

from kaso_mashin import console
from kaso_mashin.common.config import Config
from kaso_mashin.common.model import ExceptionSchema


class AbstractCommands(abc.ABC):
    """
    An abstract base class for command groups
    """

    def __init__(self, config: Config):
        self._config = config
        # TODO: We should move this into late_config with config
        self._server_url = f'http://{self.config.default_server_host}:{self.config.default_server_port}'
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
        return self._config

    @property
    def server_url(self) -> str:
        return self._server_url
