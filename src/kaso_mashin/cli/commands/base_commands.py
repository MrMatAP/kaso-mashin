import abc
import logging
import typing
import argparse

import pydantic
import httpx
import rich.table
import rich.box

from kaso_mashin import console
from kaso_mashin.common.config import Config
from kaso_mashin.common.ddd_scaffold import T_EntityListSchema, T_EntityGetSchema
from kaso_mashin.common.base_types import ExceptionSchema, EntitySchema


class BaseCommands(typing.Generic[T_EntityListSchema, T_EntityGetSchema], abc.ABC):
    """
    An abstract base class for command groups
    """

    def __init__(self, config: Config):
        self._config = config
        self._prefix = None
        self._list_schema_type: typing.Type[T_EntityListSchema] = None
        self._get_schema_type: typing.Type[T_EntityGetSchema] = None
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.debug('Started')

    @abc.abstractmethod
    def register_commands(self, parser: argparse.ArgumentParser):
        """
        Placeholder to attach commands and parameters the command class implements
        Args:
            parser: The parser to attach the commands and parameters to
        """
        pass

    def list(self, args: argparse.Namespace) -> int:
        """
        List the entities
        Args:
            args: Command line arguments

        Returns:
            Output of the entities in listed format
        """
        del args
        resp = self._api_client(uri=f'{self.prefix}/', expected_status=[200])
        if not resp:
            return 1
        entries = self.list_schema_type.model_validate_json(resp.content)
        console.print(entries)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self._api_client(uri=f'{self.prefix}/{args.uid}',
                                expected_status=[200],
                                fallback_msg='Entity not found')
        if not resp:
            return 1
        schema = self.get_schema_type.model_validate_json(resp.content)
        console.print(schema)
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        resp = self._api_client(uri=f'{self.prefix}/{args.uid}',
                                method='DELETE',
                                expected_status=[204, 410],
                                fallback_msg='Failed to remove entity')
        if not resp:
            return 1
        if resp.status_code == 204:
            console.print(f'Removed entity with id {args.uid}')
        elif resp.status_code == 404:
            console.print(f'Entity with id {args.uid} does not exist')
        return 0

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def config(self) -> Config:
        return self._config

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def list_schema_type(self) -> typing.Type[T_EntityListSchema]:
        return self._list_schema_type

    @property
    def get_schema_type(self) -> typing.Type[T_EntityGetSchema]:
        return self._get_schema_type

    def _api_client(self,
                    uri: str,
                    schema: EntitySchema = None,
                    method: str = 'GET',
                    expected_status: typing.List = None,
                    fallback_msg: str = 'Something bad and unknown happened...') -> httpx.Response | None:
        """
        Convenience method for invoking the server API and perform error handling. Since this is specifically for the
        CLI we print a generic exception message right here if we get one.

        Args:
            uri: The relative URI to invoke
            schema: An optional body for PUT or POST requests
            method: The HTTP method, defaults to 'GET'
            expected_status: A list of HTTP status codes the client deems to be acceptable for success
            fallback_msg: A custom error message for failures

        Returns:
            The httpx response or None upon failure
        """
        try:
            if expected_status is None:
                expected_status = [200]
            content = schema.model_dump_json(exclude_unset=True) if schema is not None else None
            resp = httpx.request(url=f'{self.config.server_url}{uri}',
                                 method=method,
                                 content=content,
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
        except pydantic.ValidationError as ve:
            table = rich.table.Table(title='Validation Error', box=rich.box.ROUNDED, show_header=False)
            table.add_row('[red]Status', '422')
            table.add_row('[red]Validation Problems', 'foo')
            return None
