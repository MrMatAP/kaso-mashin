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
        self._config_file = config_file
        self.load()

    def load(self):
        if not self.config_file.exists():
            # We keep the defaults
            return
        with open(self.config_file, 'r', encoding='UTF-8') as c:
            config = yaml.load(c, Loader=Loader)
            if 'path' in config:
                self.path = config.get('path')
            if 'default_os_disk_size' in config:
                self.default_os_disk_size = config.get('default_os_disk_size')
            if 'default_phone_home_port' in config:
                self.default_phone_home_port = config.get('default_phone_home_port')

    def save(self):
        with open(self.config_file, 'w+', encoding='UTF-8') as c:
            yaml.dump({
                'path': str(self.path),
                'default_os_disk_size': self.default_os_disk_size,
                'default_phone_home_port': self._default_phone_home_port
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
    def config_file(self) -> pathlib.Path:
        return self._config_file

    @config_file.setter
    def config_file(self, value: pathlib.Path):
        self._config_file = value
        self.load()
