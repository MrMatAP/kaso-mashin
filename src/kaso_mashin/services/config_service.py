import argparse
import dataclasses
import getpass
import logging
import os
import pathlib
import typing

import pydantic
import yaml
from yaml import CLoader as Loader, CDumper as Dumper

import kaso_mashin
import kaso_mashin.base

DEFAULT_CONFIG_FILE = pathlib.Path(os.environ.get("KASO_MASHIN_CONFIG", "~/.kaso")).expanduser()
DEFAULT_PATH = pathlib.Path('~/var/kaso').expanduser()
DEFAULT_IMAGES_PATH = pathlib.Path('~/var/kaso/images').expanduser()
DEFAULT_INSTANCES_PATH = pathlib.Path('~/var/kaso/instances').expanduser()
DEFAULT_BOOTSTRAP_PATH = pathlib.Path('~/var/kaso/bootstrap').expanduser()
DEFAULT_BUTANE_PATH = pathlib.Path('/opt/homebrew/bin/butane')
DEFAULT_QEMU_IMG_PATH = pathlib.Path('/opt/homebrew/bin/qemu-img')
DEFAULT_QEMU_AARCH64_PATH = pathlib.Path('/opt/homebrew/bin/qemu-system-aarch64')
DEFAULT_K8S_MASTER_TEMPLATE_NAME = "default_k8s_master"
DEFAULT_K8S_SLAVE_TEMPLATE_NAME = "default_k8s_slave"
DEFAULT_MIN_VCPU = 0
DEFAULT_MIN_RAM = kaso_mashin.base.BinarySizedValue(0, kaso_mashin.base.BinaryScale.G)
DEFAULT_MIN_DISK = kaso_mashin.base.BinarySizedValue(0, kaso_mashin.base.BinaryScale.G)
DEFAULT_HOST_NETWORK_NAME = "default_host_network"
DEFAULT_BRIDGED_NETWORK_NAME = "default_bridged_network"
DEFAULT_SHARED_NETWORK_NAME = "default_shared_network"

@dataclasses.dataclass
class PredefinedImage:
    """
    Configuration for a predefined image
    """
    name: str
    url: str

DEFAULT_PREDEFINED_IMAGES = [
    PredefinedImage(
        name="ubuntu-bionic-arm64",
        url="https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img",
    ),
    PredefinedImage(
        name="ubuntu-focal-arm64",
        url="https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-arm64.img",
    ),
    PredefinedImage(
        name="ubuntu-jammy-arm64",
        url="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img",
    ),
    PredefinedImage(
        name="ubuntu-kinetic-arm64",
        url="https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-arm64.img",
    ),
    PredefinedImage(
        name="ubuntu-lunar-arm64",
        url="https://cloud-images.ubuntu.com/lunar/current/lunar-server-cloudimg-arm64.img",
    ),
    PredefinedImage(
        name="ubuntu-mantic-arm64",
        url="https://cloud-images.ubuntu.com/mantic/current/mantic-server-cloudimg-arm64.img",
    ),
    PredefinedImage(
        name='ubuntu-core-24-arm64',
        url='https://cdimage.ubuntu.com/ubuntu-core/24/stable/current/ubuntu-core-24-arm64.img.xz'
    ),
    PredefinedImage(
        name="freebsd-14-arm64",
        url="https://download.freebsd.org/ftp/snapshots/VM-IMAGES/14.0-CURRENT/amd64/Latest/"
            "FreeBSD-14.0-CURRENT-amd64.qcow2.xz",
    ),
    PredefinedImage(
        name="flatcar-arm64",
        url="https://stable.release.flatcar-linux.net/arm64-usr/current/flatcar_production_qemu_uefi_image.img",
    ),
    PredefinedImage(
        name="flatcar-amd64",
        url="https://stable.release.flatcar-linux.net/amd64-usr/current/flatcar_production_qemu_image.img",
    )
]

class CLIArgumentsHolder(argparse.Namespace):
    """
    A typed object to receive server CLI arguments
    """

    def __init__(self, config: "ConfigService"):
        super().__init__()
        self.debug: bool = False
        self.config: pathlib.Path = DEFAULT_CONFIG_FILE
        self.host: str = config.default_server_host
        self.port: int = config.default_server_port
        self.cmd: typing.Callable | None = None


@dataclasses.dataclass(init=False)
class ConfigService:
    """
    Configuration handling for kaso_mashin
    """

    path: pathlib.Path = dataclasses.field(default=DEFAULT_PATH)
    images_path: pathlib.Path = dataclasses.field(default=DEFAULT_IMAGES_PATH)
    instances_path: pathlib.Path = dataclasses.field(default=DEFAULT_INSTANCES_PATH)
    bootstrap_path: pathlib.Path = dataclasses.field(default=DEFAULT_BOOTSTRAP_PATH)
    effective_user: str = dataclasses.field(default=getpass.getuser())
    owning_user: str = dataclasses.field(default=os.environ.get("SUDO_USER", getpass.getuser()))
    db_owning_user: str = dataclasses.field(default=os.environ.get("SUDO_USER", getpass.getuser()))
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
    uefi_code_path: path = dataclasses.field(default=DEFAULT_BOOTSTRAP_PATH / "uefi-code.fd")
    uefi_vars_path: pathlib.Path = dataclasses.field(default=DEFAULT_BOOTSTRAP_PATH / "uefi-vars.fd")
    butane_path: pathlib.Path = dataclasses.field(default=DEFAULT_BUTANE_PATH)
    qemu_img_path: pathlib.Path = dataclasses.field(default=DEFAULT_QEMU_IMG_PATH)
    qemu_aarch64_path: pathlib.Path = dataclasses.field(default=DEFAULT_QEMU_AARCH64_PATH)
    predefined_images: typing.List[PredefinedImage] = dataclasses.field(default_factory=list)

    def __init__(self, config_file: pathlib.Path | None = None):
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.predefined_images = DEFAULT_PREDEFINED_IMAGES
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
            raise kaso_mashin.base.KasoMashinException(status=400, msg="Invalid config file") from exc

    def cli_override(self, args: CLIArgumentsHolder):
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
        configured = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        try:
            with open(config_file, "w+", encoding="UTF-8") as c:
                yaml.dump(configured, c, Dumper=Dumper)
        except yaml.YAMLError as exc:
            raise kaso_mashin.base.KasoMashinException(status=500, msg="Failed to save config file") from exc

    @property
    def server_url(self) -> str:
        """
        Convenience property to calculate a server URL based on configuration suitable for httpx/requests
        Returns:
            The server URL to communicate with
        """
        return f"http://{self.default_server_host}:{self.default_server_port}"


class PredefinedImageSchema(kaso_mashin.base.EntitySchema):
    """
    Schema for a predefined image
    """

    name: str = pydantic.Field(description="Name of the predefined image")
    url: str = pydantic.Field(description="URL of the predefined image")


class ConfigSchema(kaso_mashin.base.EntitySchema):
    """
    Configuration Schema
    """

    version: str = pydantic.Field(
        description="The version of the kaso-mashin server",
        examples=["1.0.0"],
        default=kaso_mashin.__version__,
    )
    path: pathlib.Path = pydantic.Field(
        description="Path on the local disk where Kaso Mashin keeps its files"
    )
    images_path: pathlib.Path = pydantic.Field(
        description="Path on the local disk where OS images are stored"
    )
    instances_path: pathlib.Path = pydantic.Field(
        description="Path on the local disk where instances are stored"
    )
    bootstrap_path: pathlib.Path = pydantic.Field(
        description="Path on the local disk where bootstrap templates are stored"
    )
    default_os_disk_size: str = pydantic.Field(description="Default OS disk size", examples=["5G"])
    default_phone_home_port: int = pydantic.Field(
        description="Default phone home port", examples=[10200]
    )
    default_host_network_dhcp4_start: str = pydantic.Field(
        description="Default host network dhcp4 start", examples=["172.16.4.10"]
    )
    default_host_network_dhcp4_end: str = pydantic.Field(
        description="Default host network dhcp4 end", examples=["172.16.4.254"]
    )
    default_shared_network_dhcp4_start: str = pydantic.Field(
        description="Default shared network dhcp4 start", examples=["172.16.5.10"]
    )
    default_shared_network_dhcp4_end: str = pydantic.Field(
        description="Default shared network dhcp4 end", examples=["172.16.5.254"]
    )
    default_host_network_cidr: str = pydantic.Field(
        description="Default host network cidr", examples=["172.16.4.0/24"]
    )
    default_shared_network_cidr: str = pydantic.Field(
        description="Default shared network cidr", examples=["172.16.5.254/24"]
    )
    default_server_host: str = pydantic.Field(
        description="Default server host", examples=["127.0.0.1"]
    )
    default_server_port: int = pydantic.Field(description="Default server port", examples=[8000])
    uefi_code_url: str = pydantic.Field(description="URL to the UEFI code")
    uefi_vars_url: str = pydantic.Field(description="URL to the UEFI vars")
    butane_path: pathlib.Path = pydantic.Field(description="Path the local butane installation")
    qemu_aarch64_path: pathlib.Path = pydantic.Field(
        description="Path to the local qemu-aarch64 installation"
    )
    predefined_images: typing.List[PredefinedImageSchema] = pydantic.Field(
        description="List of predefined images", default=[]
    )
