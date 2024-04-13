import abc
import logging
import typing
import argparse
import httpx
import rich.table
import rich.box

from kaso_mashin import console
from kaso_mashin.common.config import Config
from kaso_mashin.common.base_types import ExceptionSchema


class AbstractCommands(abc.ABC):
    """
    An abstract base class for command groups
    """

    def __init__(self, config: Config):
        self._config = config
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.debug('Started')

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abc.abstractmethod
    def register_commands(self, parser: argparse.ArgumentParser):
        """
        Placeholder to attach commands and parameters the command class implements
        Args:
            parser: The parser to attach the commands and parameters to
        """
        pass

    def api_client(self,
                   uri: str,
                   body: typing.Dict | typing.List = None,
                   method: str = 'GET',
                   expected_status: typing.List = None,
                   fallback_msg: str = 'Something bad and unknown happened...') -> httpx.Response | None:
        """
        Convenience method for invoking the server API and perform error handling. Since this is specifically for the
        CLI we print a generic exception message right here if we get one.

        Args:
            uri: The relative URI to invoke
            body: An optional body for PUT or POST requests
            method: The HTTP method, defaults to 'GET'
            expected_status: A list of HTTP status codes the client deems to be acceptable for success
            fallback_msg: A custom error message for failures

        Returns:
            The httpx response or None upon failure
        """
        if expected_status is None:
            expected_status = [200]
        resp = httpx.request(url=f'{self.config.server_url}{uri}',
                             method=method,
                             json=body,
                             timeout=120)
        if resp.status_code not in expected_status:
            table = rich.table.Table(title='ERROR', box=rich.box.ROUNDED, show_header=False)
            table.add_row('[red]Status:', str(resp.status_code))
            try:
                ex = ExceptionSchema.model_validate_json(resp.content)
                table.add_row('[red]Message:', ex.msg)
            except ValueError:
                table.add_row('[red]Message:', fallback_msg)
            console.print(table)
            return None
        return resp

    @property
    def config(self) -> Config:
        return self._config

