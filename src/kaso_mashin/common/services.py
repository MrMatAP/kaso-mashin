import argparse
import asyncio
import dataclasses
import logging
import pathlib
import subprocess
import typing
import uuid

import yaml
from aievents import Events
from yaml import CLoader as Loader, CDumper as Dumper

from .base import (
    UniqueIdentifier,
    BinarySizedValue, BinaryScale,
    Service
)
from .types import (
    BootstrapKind,
    TaskState, TaskRelation
)
from .exceptions import (
    KasoMashinException,
    EntityInvariantException,
    EntityNotFoundException
)
from kaso_mashin import default_config_file


class EventService(Service, Events):
    """
    To subscribe:
    self.runtime.event_service.on_task_fail += <local async method>
    To emit:
    await self.runtime.event_service.on_task_fail(self)
    """
    __events__ = ("on_task_create", "on_task_progress", "on_task_done", "on_task_fail")

    def __init__(self):
        super().__init__()
        self._logger.info("Started messaging service")


class QEMUService(Service):

    def __init__(self):
        super().__init__()
        self._logger.info("Started QEMU service")

    def start_instance(self, instance: 'InstanceEntity') -> subprocess.Popen:
        try:
            args = [
                str(self._runtime.config.qemu_aarch64_path),
                "-name",
                instance.name,
                "-machine",
                "virt",
                "-cpu",
                "host",
                "-accel",
                "hvf",
                "-m",
                str(instance.ram.at_scale(BinaryScale.M).value),
                "-smp",
                str(instance.vcpu),
                "-object",
                "rng-random,id=rng0,filename=/dev/urandom",
                "-device",
                "virtio-rng-pci,rng=rng0",
                "-device",
                "virtio-gpu-pci",
                "-device",
                "nec-usb-xhci,id=usb-bus",
                "-device",
                "usb-kbd,bus=usb-bus.0",
                "-netdev",
                f"{instance.network.kind.value},"
                f"id=net0,"
                f"start-address={instance.network.dhcp_start},"
                f"end-address={instance.network.dhcp_end},"
                f"subnet-mask={instance.network.netmask}",
                "-device",
                f"virtio-net-device,netdev=net0,mac={instance.mac}",
                "-drive",
                f"if=virtio,file={instance.os_disk.path},format=qcow2,index=0,media=disk",
            ]
            # Add options for forwarding the serial console and mon
            # TODO: We're doing telnet for now until we can hookup the frontends to this
            # TODO: This actually works with telnet when you expose it via
            #       sudo socat UNIX:/path/to/console.sock TCP-LISTEN:5701
            args.extend([
                "-nographic",
                "-chardev",
                f"socket,id=char0,server=on,wait=off,telnet=on,path={instance.path.joinpath('console.sock')}",
                "-serial",
                "chardev:char0"
                "-chardev",
                f"socket,id=char1,server=on,wait=off,telnet=on,path={instance.path.joinpath('qmp.sock')}",
                "-mon",
                "chardev=char1,mode=readline",
            ])
            if instance.bootstrap.kind == BootstrapKind.IGNITION:
                args.extend(
                    [
                        "-fw_cfg",
                        f"name=opt/org.flatcar-linux/config,file={instance.bootstrap_file}",
                        "-drive",
                        f"if=pflash,file={instance.uefi_code},format=raw,readonly=on",
                        "-drive",
                        f"if=pflash,file={instance.uefi_vars},format=raw",
                    ]
                )
            if instance.bootstrap.kind == BootstrapKind.CLOUD_INIT:
                raise KasoMashinException(status=500, msg="Bootstrap init not supported")

            return subprocess.Popen(args)
        except Exception as e:
            raise KasoMashinException(status=500, msg=str(e))


class Task:
    """
    Domain model entity for a task
    """

    def __init__(self,
                 name: str,
                 relation: TaskRelation = TaskRelation.GENERAL,
                 msg: str = "Task created"):
        self._uid = uuid.uuid4()
        self._name = name
        self._relation = relation
        self._state = TaskState.INITIALIZED
        self._msg = msg
        self._percent_complete = 0
        self._task: asyncio.Task | None = None
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    def uid(self) -> UniqueIdentifier:
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    @property
    def relation(self) -> TaskRelation:
        return self._relation

    @property
    def state(self) -> TaskState:
        return self._state

    @state.setter
    def state(self, value: TaskState):
        self._state = value

    @property
    def msg(self) -> str:
        return self._msg

    @property
    def percent_complete(self) -> int:
        return self._percent_complete

    @property
    def task(self) -> asyncio.Task:
        return self._task

    @task.setter
    def task(self, value: asyncio.Task) -> None:
        self._task = value

    async def run(self, *args, **kwargs):
        self._state = 'Task running'
        self._state = TaskState.RUNNING
        self._logger.info(f'Task {self._uid} running: {self._msg}')

    async def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._msg = 'Task cancelled'
            self._state = TaskState.CANCELLED
            self._logger.info(f'Task {self._uid} cancelled: {self._msg}')

    def __eq__(self, other: typing.Any) -> bool:
        return all(
            [
                super().__eq__(other),
                self._uid == other.uid,
                self._name == other.name,
                self._relation == other.relation,
                self._state == other.state,
                self._msg == other.msg,
                self._percent_complete == other.percent_complete,
            ]
        )

    def __lt__(self, other: typing.Any) -> bool:
        return self.uid < other.uid

    async def progress(self, percent_complete: int, msg: str | None = None) -> None:
        self._percent_complete = percent_complete
        if msg is not None:
            self._msg = msg

    async def done(self, msg: str = 'Task done'):
        self._percent_complete = 100
        self._msg = msg
        self._state = TaskState.DONE
        self._logger.debug(f'Task {self._uid} done')

    async def fail(self, msg: str = 'Task failed'):
        self._msg = msg
        self._state = TaskState.FAILED
        self._logger.debug(f'Task {self._uid} failed: {self._msg}')

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(uid={self.uid}, "
            f"name={self.name}, "
            f'relation={self.relation}, '
            f"state={self.state}, "
            f"msg={self.msg}, "
            f"percent_complete={self.percent_complete}"
            f")")


class TaskService:
    """
    A repository of tasks
    """

    def __init__(self):
        Task.repository = self
        self._identity_map: typing.Dict[UniqueIdentifier, Task] = {}

    def get_by_uid(self, uid: UniqueIdentifier) -> Task:
        if uid not in self._identity_map:
            raise EntityNotFoundException()
        return self._identity_map[uid]

    def get_by_state(self, state: TaskState) -> typing.List[Task]:
        return list(filter(lambda x: x.state == state, self._identity_map.values()))

    def list(self) -> typing.List[Task]:
        return list(self._identity_map.values())

    def create(self, entity: Task, *args, **kwargs) -> Task:
        if entity.uid in self._identity_map:
            raise EntityInvariantException(status=400, msg="Task already exists")
        self._identity_map[entity.uid] = entity
        entity.task = asyncio.create_task(entity.run(*args, **kwargs))
        return self._identity_map[entity.uid]

    def remove(self, uid: UniqueIdentifier):
        if uid not in self._identity_map:
            raise EntityNotFoundException()
        del self._identity_map[uid]


class CLIArgumentsHolder(argparse.Namespace):
    """
    A typed object to receive server CLI arguments
    """

    def __init__(self, config: "ConfigService"):
        super().__init__()
        self.debug: bool = False
        self.config: pathlib.Path = default_config_file
        self.host: str = config.default_server_host
        self.port: int = config.default_server_port
        self.cmd: typing.Callable | None = None

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

DEFAULT_PATH = pathlib.Path('~/var/kaso').expanduser()
DEFAULT_IMAGES_PATH = pathlib.Path('~/var/kaso/images').expanduser()
DEFAULT_INSTANCES_PATH = pathlib.Path('~/var/kaso/instances').expanduser()
DEFAULT_BOOTSTRAP_PATH = pathlib.Path('~/var/kaso/bootstrap').expanduser()
DEFAULT_K8S_MASTER_TEMPLATE_NAME = "default_k8s_master"
DEFAULT_K8S_SLAVE_TEMPLATE_NAME = "default_k8s_slave"
DEFAULT_MIN_VCPU = 0
DEFAULT_MIN_RAM = BinarySizedValue(0, BinaryScale.G)
DEFAULT_MIN_DISK = BinarySizedValue(0, BinaryScale.G)
DEFAULT_MAC_PREFIX = "00:50:56"
DEFAULT_HOST_NETWORK_NAME = "default_host_network"
DEFAULT_BRIDGED_NETWORK_NAME = "default_bridged_network"
DEFAULT_SHARED_NETWORK_NAME = "default_shared_network"
DEFAULT_BUTANE_PATH = pathlib.Path('/opt/homebrew/bin/butane')
DEFAULT_QEMU_IMG_PATH = pathlib.Path('/opt/homebrew/bin/qemu-img')
DEFAULT_QEMU_AARCH64_PATH = pathlib.Path('/opt/homebrew/bin/qemu-system-aarch64')

@dataclasses.dataclass(init=False)
class ConfigService:
    """
    Configuration handling for kaso_mashin
    """

    path: pathlib.Path = dataclasses.field(default=DEFAULT_PATH)
    images_path: pathlib.Path = dataclasses.field(default=DEFAULT_IMAGES_PATH)
    instances_path: pathlib.Path = dataclasses.field(default=DEFAULT_INSTANCES_PATH)
    bootstrap_path: pathlib.Path = dataclasses.field(default=DEFAULT_BOOTSTRAP_PATH)
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
            raise KasoMashinException(status=400, msg="Invalid config file") from exc

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
            raise KasoMashinException(status=500, msg="Failed to save config file") from exc

    @property
    def server_url(self) -> str:
        """
        Convenience property to calculate a server URL based on configuration suitable for httpx/requests
        Returns:
            The server URL to communicate with
        """
        return f"http://{self.default_server_host}:{self.default_server_port}"
