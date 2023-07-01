import pathlib

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper      # pylint: disable=unused-import
except ImportError:
    from yaml import Loader, Dumper                 # pylint: disable=unused-import


class Config:
    """
    Configuration handling for kaso_mashin
    """

    def __init__(self, config_file: pathlib.Path):
        self._path = pathlib.Path('~/var/kaso').expanduser()
        self._default_os_disk_size = '5G'
        self._default_phone_home_port = 10200
        self._default_host_network_dhcp_start = '172.16.4.10'
        self._default_host_network_dhcp_end = '172.16.4.254'
        self._default_shared_network_dhcp_start = '172.16.5.10'
        self._default_shared_network_dhcp_end = '172.16.5.254'
        self._default_host_network_cidr = '172.16.4.0/24'
        self._default_shared_network_cidr = '172.16.5.0/24'
        self._config_file = config_file
        self.load()

    def load(self):
        if not self.config_file.exists():
            # We keep the defaults
            return
        with open(self.config_file, 'r', encoding='UTF-8') as c:
            config = yaml.load(c, Loader=Loader)
            if 'path' in config:
                self.path = pathlib.Path(config.get('path'))
            if 'default_os_disk_size' in config:
                self.default_os_disk_size = config.get('default_os_disk_size')
            if 'default_phone_home_port' in config:
                self.default_phone_home_port = config.get('default_phone_home_port')
            if 'default_host_network_dhcp_start' in config:
                self.default_host_network_dhcp_start = config.get('default_host_network_dhcp_start')
            if 'default_host_network_dhcp_end' in config:
                self.default_host_network_dhcp_end = config.get('default_host_network_dhcp_end')
            if 'default_shared_network_dhcp_start' in config:
                self.default_shared_network_dhcp_start = config.get('default_shared_network_dhcp_start')
            if 'default_shared_network_dhcp_end' in config:
                self.default_shared_network_dhcp_end = config.get('default_shared_network_dhcp_end')
            if 'default_host_network_cidr' in config:
                self.default_host_network_cidr = config.get('default_host_network_cidr')
            if 'default_shared_network_cidr' in config:
                self.default_shared_network_cidr = config.get('default_shared_network_cidr')

    def save(self):
        with open(self.config_file, 'w+', encoding='UTF-8') as c:
            yaml.dump({
                'path': str(self.path),
                'default_os_disk_size': self.default_os_disk_size,
                'default_phone_home_port': self._default_phone_home_port,
                'default_host_network_dhcp_start': self._default_host_network_dhcp_start,
                'default_host_network_dhcp_end': self._default_host_network_dhcp_end,
                'default_shared_network_dhcp_start': self._default_shared_network_dhcp_start,
                'default_shared_network_dhcp_end': self._default_shared_network_dhcp_end,
                'default_host_network_cidr': self._default_host_network_cidr,
                'default_shared_network_cidr': self._default_shared_network_cidr,
            }, c, Dumper=Dumper)

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @path.setter
    def path(self, value: pathlib.Path):
        self._path = value

    @property
    def default_os_disk_size(self) -> str:
        return self._default_os_disk_size

    @default_os_disk_size.setter
    def default_os_disk_size(self, value: str):
        self._default_os_disk_size = value

    @property
    def default_phone_home_port(self) -> int:
        return self._default_phone_home_port

    @default_phone_home_port.setter
    def default_phone_home_port(self, value: int):
        self._default_phone_home_port = value

    @property
    def default_host_network_dhcp_start(self) -> str:
        return self._default_host_network_dhcp_start

    @default_host_network_dhcp_start.setter
    def default_host_network_dhcp_start(self, value: str):
        self._default_host_network_dhcp_start = value

    @property
    def default_host_network_dhcp_end(self) -> str:
        return self._default_host_network_dhcp_end

    @default_host_network_dhcp_end.setter
    def default_host_network_dhcp_end(self, value: str):
        self._default_host_network_dhcp_end = value

    @property
    def default_shared_network_dhcp_start(self) -> str:
        return self._default_shared_network_dhcp_start

    @default_shared_network_dhcp_start.setter
    def default_shared_network_dhcp_start(self, value: str):
        self._default_shared_network_dhcp_start = value

    @property
    def default_shared_network_dhcp_end(self) -> str:
        return self._default_shared_network_dhcp_end

    @default_shared_network_dhcp_end.setter
    def default_shared_network_dhcp_end(self, value: str):
        self._default_shared_network_dhcp_end = value

    @property
    def default_host_network_cidr(self) -> str:
        return self._default_host_network_cidr

    @default_host_network_cidr.setter
    def default_host_network_cidr(self, value: str):
        self._default_host_network_cidr = value

    @property
    def default_shared_network_cidr(self) -> str:
        return self._default_shared_network_cidr

    @default_shared_network_cidr.setter
    def default_shared_network_cidr(self, value: str):
        self._default_shared_network_cidr = value

    @property
    def config_file(self) -> pathlib.Path:
        return self._config_file

    @config_file.setter
    def config_file(self, value: pathlib.Path):
        self._config_file = value
        self.load()
