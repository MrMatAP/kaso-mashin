import argparse
import logging
import pathlib
import dataclasses

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper      # pylint: disable=unused-import
except ImportError:
    from yaml import Loader, Dumper                 # pylint: disable=unused-import

from kaso_mashin import KasoMashinException


@dataclasses.dataclass(init=False)
class Config:
    """
    Configuration handling for kaso_mashin
    """
    path: pathlib.Path = dataclasses.field(default=pathlib.Path('~/var/kaso').expanduser())
    default_os_disk_size: str = dataclasses.field(default='5G')
    default_phone_home_port: int = dataclasses.field(default=10200)
    default_host_network_dhcp4_start: str = dataclasses.field(default='172.16.4.10')
    default_host_network_dhcp4_end: str = dataclasses.field(default='172.16.4.254')
    default_shared_network_dhcp4_start: str = dataclasses.field(default='172.16.5.10')
    default_shared_network_dhcp4_end: str = dataclasses.field(default='172.16.5.254')
    default_host_network_cidr: str = dataclasses.field(default='172.16.4.0/24')
    default_shared_network_cidr: str = dataclasses.field(default='172.16.5.0/24')
    default_server_host: str = dataclasses.field(default='127.0.0.1')
    default_server_port: int = dataclasses.field(default=8000)

    def __init__(self, config_file: pathlib.Path = None):
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        if config_file:
            self.load(config_file)

    def load(self, config_file: pathlib.Path):
        """
        Override the defaults from a config file if it exists
        """
        if not config_file.exists():
            self._logger.debug('No configuration file exists, using defaults')
            return
        self._logger.debug('Loading config file at %s', config_file)
        configurable = {field.name: field.type for field in dataclasses.fields(self)}
        try:
            with open(config_file, 'r', encoding='UTF-8') as c:
                configured = yaml.load(c, Loader=Loader)
                # Set the values for the intersection of what is configurable and actually configured
            for key in list(set(configurable.keys()) & set(configured.keys())):
                value = configured.get(key)
                if configurable.get(key) == pathlib.Path:
                    setattr(self, key, pathlib.Path(value))
                else:
                    setattr(self, key, value)
                self._logger.debug('Config file overrides %s to %s', key, value)
        except yaml.YAMLError as exc:
            raise KasoMashinException(status=400, msg='Invalid config file') from exc

    def cli_override(self, args: argparse.Namespace):
        """
        Override the defaults and what has been set in the config file with CLI arguments
        Args:
            args: The CLI arguments
        """
        configurable = {field.name: field.type for field in dataclasses.fields(self)}
        configured = vars(args)
        for key in list(set(configurable.keys()) & set(configured.keys())):
            value = configured.get(key)
            if value != getattr(self, key):
                setattr(self, key, value)
                self._logger.debug('CLI overrides %s to %s', key, value)

    def save(self, config_file: pathlib.Path):
        self._logger.debug('Saving configuration at %s', config_file)
        configured = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        try:
            with open(config_file, 'w+', encoding='UTF-8') as c:
                yaml.dump(configured, c, Dumper=Dumper)
        except yaml.YAMLError as exc:
            raise KasoMashinException(status=500, msg='Failed to save config file') from exc

    @property
    def server_url(self) -> str:
        """
        Convenience property to calculate a server URL based on configuration suitable for httpx/requests
        Returns:
            The server URL to communicate with
        """
        return f'http://{self.default_server_host}:{self.default_server_port}'
