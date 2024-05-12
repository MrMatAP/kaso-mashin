import argparse
import logging
import pathlib
import dataclasses
import typing

import pydantic
import yaml

from kaso_mashin.common import EntitySchema

try:
    from yaml import (
        CLoader as Loader,
        CDumper as Dumper,
    )  # pylint: disable=unused-import
except ImportError:
    from yaml import Loader, Dumper  # pylint: disable=unused-import

from kaso_mashin import __version__, KasoMashinException


class PredefinedImageSchema(EntitySchema):
    """
    Schema for a predefined image
    """
    name: str = pydantic.Field(description='Name of the predefined image')
    url: str = pydantic.Field(description='URL of the predefined image')


class ConfigSchema(EntitySchema):
    """
    Configuration Schema
    """

    version: str = pydantic.Field(
        description="The version of the kaso-mashin server", examples=["1.0.0"], default=__version__
    )
    path: pathlib.Path = pydantic.Field(description='Path on the local disk where Kaso Mashin keeps its files')
    images_path: pathlib.Path = pydantic.Field(description='Path on the local disk where OS images are stored')
    instances_path: pathlib.Path = pydantic.Field(description='Path on the local disk where instances are stored')
    bootstrap_path: pathlib.Path = pydantic.Field(
        description='Path on the local disk where bootstrap templates are stored')
    default_os_disk_size: str = pydantic.Field(description='Default OS disk size', examples=["5G"])
    default_phone_home_port: int = pydantic.Field(description='Default phone home port', examples=[10200])
    default_host_network_dhcp4_start: str = pydantic.Field(description='Default host network dhcp4 start',
                                                           examples=["172.16.4.10"])
    default_host_network_dhcp4_end: str = pydantic.Field(description='Default host network dhcp4 end',
                                                         examples=["172.16.4.254"])
    default_shared_network_dhcp4_start: str = pydantic.Field(description='Default shared network dhcp4 start',
                                                             examples=["172.16.5.10"])
    default_shared_network_dhcp4_end: str = pydantic.Field(description='Default shared network dhcp4 end',
                                                           examples=["172.16.5.254"])
    default_host_network_cidr: str = pydantic.Field(description='Default host network cidr', examples=["172.16.4.0/24"])
    default_shared_network_cidr: str = pydantic.Field(description='Default shared network cidr',
                                                      examples=["172.16.5.254/24"])
    default_server_host: str = pydantic.Field(description='Default server host', examples=["127.0.0.1"])
    default_server_port: int = pydantic.Field(description='Default server port', examples=[8000])
    uefi_code_url: str = pydantic.Field(description='URL to the UEFI code')
    uefi_vars_url: str = pydantic.Field(description='URL to the UEFI vars')
    butane_path: pathlib.Path = pydantic.Field(description='Path the local butane installation')
    qemu_aarch64_path: pathlib.Path = pydantic.Field(description='Path to the local qemu-aarch64 installation')
    predefined_images: typing.List[PredefinedImageSchema] = pydantic.Field(
        description="List of predefined images", default=[]
    )


Predefined_Images = [
    PredefinedImageSchema(name="ubuntu-bionic",
                          url="https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img"),
    PredefinedImageSchema(name="ubuntu-focal",
                          url="https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-arm64.img"),
    PredefinedImageSchema(name="ubuntu-jammy",
                          url="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img"),
    PredefinedImageSchema(name="ubuntu-kinetic",
                          url="https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-arm64.img"),
    PredefinedImageSchema(name="ubuntu-lunar",
                          url="https://cloud-images.ubuntu.com/lunar/current/lunar-server-cloudimg-arm64.img"),
    PredefinedImageSchema(name="ubuntu-mantic",
                          url="https://cloud-images.ubuntu.com/mantic/current/mantic-server-cloudimg-arm64.img"),
    PredefinedImageSchema(name="freebsd-14",
                          url="https://download.freebsd.org/ftp/snapshots/VM-IMAGES/14.0-CURRENT/amd64/Latest/"
                              "FreeBSD-14.0-CURRENT-amd64.qcow2.xz"),
    PredefinedImageSchema(name="flatcar-arm64",
                          url="https://stable.release.flatcar-linux.net/arm64-usr/current/flatcar_production_qemu_uefi_image.img"),
    PredefinedImageSchema(name="flatcar-amd64",
                          url="https://stable.release.flatcar-linux.net/amd64-usr/current/flatcar_production_qemu_image.img")
]



@dataclasses.dataclass(init=False)
class Config:
    """
    Configuration handling for kaso_mashin
    """

    path: pathlib.Path = dataclasses.field(
        default=pathlib.Path("~/var/kaso").expanduser()
    )
    images_path: pathlib.Path = dataclasses.field(
        default=pathlib.Path("~/var/kaso/images").expanduser()
    )
    instances_path: pathlib.Path = dataclasses.field(
        default=pathlib.Path("~/var/kaso/instances").expanduser()
    )
    bootstrap_path: pathlib.Path = dataclasses.field(
        default=pathlib.Path("~/var/kaso/bootstrap").expanduser()
    )
    default_os_disk_size: str = dataclasses.field(default="5G")
    default_phone_home_port: int = dataclasses.field(default=10200)
    default_host_network_dhcp4_start: str = dataclasses.field(default="172.16.4.10")
    default_host_network_dhcp4_end: str = dataclasses.field(default="172.16.4.254")
    default_shared_network_dhcp4_start: str = dataclasses.field(default="172.16.5.10")
    default_shared_network_dhcp4_end: str = dataclasses.field(default="172.16.5.254")
    default_host_network_cidr: str = dataclasses.field(default="172.16.4.0/24")
    default_shared_network_cidr: str = dataclasses.field(default="172.16.5.0/24")
    default_server_host: str = dataclasses.field(default="127.0.0.1")
    default_server_port: int = dataclasses.field(default=8000)
    uefi_code_url: str = dataclasses.field(
        default="https://stable.release.flatcar-linux.net/arm64-usr/current/flatcar_production_qemu_uefi_efi_code.fd"
    )
    uefi_vars_url: str = dataclasses.field(
        default="https://stable.release.flatcar-linux.net/arm64-usr/current/flatcar_production_qemu_uefi_efi_vars.fd"
    )
    butane_path: pathlib.Path = dataclasses.field(
        default=pathlib.Path("/opt/homebrew/bin/butane")
    )
    qemu_aarch64_path: pathlib.Path = dataclasses.field(
        default=pathlib.Path("/opt/homebrew/bin/qemu-system-aarch64")
    )
    predefined_images: typing.List[PredefinedImageSchema] = dataclasses.field(default_factory=list)

    def __init__(self, config_file: typing.Optional[pathlib.Path] = None):
        self._logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self.predefined_images = Predefined_Images
        if config_file:
            self.load(config_file)

    def load(self, config_file: pathlib.Path):
        """
        Override the defaults from a config file if it exists
        """
        if not config_file.exists():
            self._logger.debug("No configuration file exists, using defaults")
            return
        self._logger.debug("Loading config file at %s", config_file)
        configurable = {field.name: field.type for field in dataclasses.fields(self)}
        try:
            with open(config_file, "r", encoding="UTF-8") as c:
                configured = yaml.load(c, Loader=Loader)
                # Set the values for the intersection of what is configurable and actually configured
            for key in list(set(configurable.keys()) & set(configured.keys())):
                value = configured.get(key)
                if configurable.get(key) == pathlib.Path:
                    setattr(self, key, pathlib.Path(value))
                else:
                    setattr(self, key, value)
                self._logger.debug("Config file overrides %s to %s", key, value)
        except yaml.YAMLError as exc:
            raise KasoMashinException(status=400, msg="Invalid config file") from exc

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
                self._logger.debug("CLI overrides %s to %s", key, value)

    def save(self, config_file: pathlib.Path):
        self._logger.debug("Saving configuration at %s", config_file)
        configured = {
            field.name: getattr(self, field.name) for field in dataclasses.fields(self)
        }
        try:
            with open(config_file, "w+", encoding="UTF-8") as c:
                yaml.dump(configured, c, Dumper=Dumper)
        except yaml.YAMLError as exc:
            raise KasoMashinException(
                status=500, msg="Failed to save config file"
            ) from exc

    @property
    def server_url(self) -> str:
        """
        Convenience property to calculate a server URL based on configuration suitable for httpx/requests
        Returns:
            The server URL to communicate with
        """
        return f"http://{self.default_server_host}:{self.default_server_port}"
