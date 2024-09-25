import asyncio
import logging
import subprocess
import typing
import uuid

from aievents import Events

from .base import Service, UniqueIdentifier
from .types import (
    BinaryScale,
    BootstrapKind,
    TaskState,
    TaskRelation
)
from .exceptions import (
    KasoMashinException,
    EntityInvariantException,
    EntityNotFoundException
)


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
        self._logger.info(f'Task {self._uid} running: {self._msg}')
        self._state = TaskState.RUNNING

    async def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()

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
