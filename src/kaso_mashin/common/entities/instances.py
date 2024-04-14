import typing
import enum
import re
import pathlib
import shutil

from pydantic import Field

from sqlalchemy import String, Integer, Enum, UUID
from sqlalchemy.orm import Mapped, mapped_column

import rich.table
import rich.box

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntitySchema,
    EntityModel,
    Entity,
    AggregateRoot,
    AsyncRepository,
    BinarySizedValue,
    BinaryScale,
)

from kaso_mashin.common.entities import (
    TaskEntity,
    ImageEntity,
    DiskEntity,
    DiskFormat,
    DiskGetSchema,
    NetworkEntity,
    NetworkGetSchema,
    BootstrapEntity,
    BootstrapGetSchema,
)


class InstanceState(str, enum.Enum):
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    STARTED = "STARTED"


MAC_VENDOR_PREFIX = "00:50:56"


class InstanceListEntrySchema(EntitySchema):
    """
    Schema for an instance list
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier of the instance",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(
        description="The instance name", examples=["k8s-master", "your-mom"]
    )


class InstanceListSchema(EntitySchema):
    """
    Schema to list instances
    """

    entries: typing.List[InstanceListEntrySchema] = Field(
        description="List of instances", default_factory=list
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Name")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name)
        return table


class InstanceCreateSchema(EntitySchema):
    """
    Schema to create an instance
    """

    name: str = Field(
        description="The instance name", examples=["k8s-master", "your-mom"]
    )
    vcpu: int = Field(description="Number of virtual CPU cores", examples=[2])
    ram: BinarySizedValue = Field(
        description="Amount of RAM", examples=[BinarySizedValue(2, BinaryScale.G)]
    )
    os_disk_size: BinarySizedValue = Field(description="Size of the OS disk")
    image_uid: str = Field(
        description="The image UID from which to create the OS disk from",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    network_uid: str = Field(
        description="The network on which to run this instance",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    bootstrap_uid: str = Field(
        description="The bootstrap uid",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )


class InstanceGetSchema(EntitySchema):
    """
    Schema to get information about a specific instance
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier of the instance",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(
        description="The instance name", examples=["k8s-master", "your-mom"]
    )
    path: pathlib.Path = Field(description="Path of the instance on the local disk")
    vcpu: int = Field(description="Number of virtual CPU cores", examples=[2])
    ram: BinarySizedValue = Field(
        description="Amount of RAM", examples=[BinarySizedValue(2, BinaryScale.G)]
    )
    mac: str = Field(description="Instance MAC address")
    os_disk: DiskGetSchema = Field(
        description="The image from which to create the OS disk from"
    )
    network: NetworkGetSchema = Field(
        description="The network on which to run this instance"
    )
    bootstrap: BootstrapGetSchema = Field(description="The bootstrapper")
    bootstrap_file: pathlib.Path = Field(
        description="The path to the bootstrap file on the local disk"
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Path", str(self.path))
        table.add_row("[blue]VCPUs", str(self.vcpu))
        table.add_row("[blue]RAM", f"{self.ram.value} {self.ram.scale}")
        table.add_row("[blue]MAC", self.mac)
        table.add_row("[blue]OS Disk UID", str(self.os_disk.uid))
        table.add_row("[blue]OS Disk Path", str(self.os_disk.path))
        table.add_row("[blue]Network UID", str(self.network.uid))
        table.add_row("[blue]Network Name", self.network.name)
        table.add_row("[blue]Bootstrap UID", str(self.bootstrap.uid))
        table.add_row("[blue]Bootstrap Name", self.bootstrap.name)
        table.add_row("[blue]Bootstrap Path", str(self.bootstrap_file))
        return table


class InstanceModifySchema(EntitySchema):
    """
    Schema to modify an existing instance
    """

    state: InstanceState = Field(description="The state of the instance")


class InstanceException(KasoMashinException):
    """
    Exception for instance-related issues
    """

    pass


class InstanceModel(EntityModel):
    """
    Representation of an instance entity in the database
    """

    __tablename__ = "instances"
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    uefi_code: Mapped[str] = mapped_column(String())
    uefi_vars: Mapped[str] = mapped_column(String())
    vcpu: Mapped[int] = mapped_column(Integer, default=0)
    ram: Mapped[int] = mapped_column(Integer, default=2)
    ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    mac: Mapped[str] = mapped_column(String)
    os_disk_uid: Mapped[str] = mapped_column(
        UUID(as_uuid=True).with_variant(String(32), "sqlite")
    )
    network_uid: Mapped[str] = mapped_column(
        UUID(as_uuid=True).with_variant(String(32), "sqlite")
    )
    bootstrap_uid: Mapped[str] = mapped_column(
        UUID(as_uuid=True).with_variant(String(32), "sqlite")
    )
    bootstrap_file: Mapped[str] = mapped_column(String)


class InstanceEntity(Entity, AggregateRoot):
    """
    Domain model entity for an instance
    """

    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        uefi_code: pathlib.Path,
        uefi_vars: pathlib.Path,
        vcpu: int,
        ram: BinarySizedValue,
        os_disk: DiskEntity,
        network: NetworkEntity,
        bootstrap: BootstrapEntity,
        bootstrap_file: pathlib.Path,
    ):
        super().__init__()
        self._name = name
        self._path = path
        self._uefi_code = uefi_code
        self._uefi_vars = uefi_vars
        self._vcpu = vcpu
        self._ram = ram
        self._mac = self._generate_mac()
        self._os_disk = os_disk
        self._network = network
        self._bootstrap = bootstrap
        self._bootstrap_file = bootstrap_file
        self._popen = None
        self._state = InstanceState.STOPPED

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def uefi_code(self) -> pathlib.Path:
        return self._uefi_code

    @property
    def uefi_vars(self) -> pathlib.Path:
        return self._uefi_vars

    @property
    def vcpu(self) -> int:
        return self._vcpu

    @property
    def ram(self) -> BinarySizedValue:
        return self._ram

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def os_disk(self) -> DiskEntity:
        return self._os_disk

    @property
    def network(self) -> NetworkEntity:
        return self._network

    @property
    def bootstrap(self) -> BootstrapEntity:
        return self._bootstrap

    @property
    def bootstrap_file(self) -> pathlib.Path:
        return self._bootstrap_file

    def __eq__(self, other: "InstanceEntity") -> bool:
        return all(
            [
                super().__eq__(other),
                self.name == other.name,
                self.path == other.path,
                self.uefi_code == other.uefi_code,
                self.uefi_vars == other.uefi_vars,
                self.vcpu == other.vcpu,
                self.ram == other.ram,
                self.mac == other.mac,
                self.os_disk == other.os_disk,
                self.network == other.network,
                self.bootstrap == other.bootstrap,
                self.bootstrap_file == other.bootstrap_file,
            ]
        )

    def __repr__(self) -> str:
        return (
            f"InstanceEntity(uid={self.uid}, "
            f"name={self.name}, "
            f"path={self.path}, "
            f"uefi_code={self.uefi_code}, "
            f"uefi_vars={self.uefi_vars}, "
            f"vcpu={self.vcpu}, "
            f"ram={self.ram}, "
            f"mac={self.mac}, "
            f"os_disk={self.os_disk}, "
            f"network={self.network}, "
            f"bootstrap={self.bootstrap}, "
            f"bootstrap_file={self.bootstrap_file}"
            ")"
        )

    @staticmethod
    async def from_model(model: InstanceModel) -> "InstanceEntity":
        # TODO: Internal consistency. This will fail if the disk is dead
        os_disk = await DiskEntity.repository.get_by_uid(
            UniqueIdentifier(model.os_disk_uid)
        )
        network = await NetworkEntity.repository.get_by_uid(
            UniqueIdentifier(model.network_uid)
        )
        bootstrap = await BootstrapEntity.repository.get_by_uid(
            UniqueIdentifier(model.bootstrap_uid)
        )

        entity = InstanceEntity(
            name=model.name,
            path=pathlib.Path(model.path),
            uefi_code=pathlib.Path(model.uefi_code),
            uefi_vars=pathlib.Path(model.uefi_vars),
            vcpu=model.vcpu,
            ram=BinarySizedValue(value=model.ram, scale=BinaryScale(model.ram_scale)),
            os_disk=os_disk,
            network=network,
            bootstrap=bootstrap,
            bootstrap_file=pathlib.Path(model.bootstrap_file),
        )
        entity._uid = UniqueIdentifier(model.uid)
        entity._mac = model.mac
        return entity

    async def to_model(self, model: InstanceModel | None = None) -> InstanceModel:
        if model is None:
            return InstanceModel(
                uid=str(self.uid),
                name=self.name,
                path=str(self.path),
                uefi_code=str(self.uefi_code),
                uefi_vars=str(self.uefi_vars),
                vcpu=self.vcpu,
                ram=self.ram.value,
                ram_scale=self.ram.scale,
                mac=self.mac,
                os_disk_uid=str(self.os_disk.uid),
                network_uid=str(self.network.uid),
                bootstrap_uid=str(self.bootstrap.uid),
                bootstrap_file=str(self.bootstrap_file),
            )
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.path = str(self.path)
            model.uefi_code = str(self.uefi_code)
            model.uefi_vars = str(self.uefi_vars)
            model.vcpu = self.vcpu
            model.ram = self.ram.value
            model.ram_scale = self.ram.scale
            model.mac = str(self.mac)
            model.os_disk_uid = str(self.os_disk.uid)
            model.network_uid = str(self.network.uid)
            model.bootstrap_uid = str(self.bootstrap.uid)
            model.bootstrap_file = str(self.bootstrap_file)
            return model

    def _generate_mac(self) -> str:
        octets = re.findall("..", self.uid.hex[:6])
        return f'{MAC_VENDOR_PREFIX}:{":".join(octets)}'

    @staticmethod
    async def create(
        task: TaskEntity,
        user: str,
        name: str,
        path: pathlib.Path,
        uefi_code: pathlib.Path,
        uefi_vars: pathlib.Path,
        vcpu: int,
        ram: BinarySizedValue,
        image: ImageEntity,
        os_disk_size: BinarySizedValue,
        network: NetworkEntity,
        bootstrap: BootstrapEntity,
    ) -> "InstanceEntity":
        if path.exists():
            raise InstanceException(
                status=400, msg=f"Instance path at {path} already exists", task=task
            )
        os_disk = None
        try:
            path.mkdir(parents=True, exist_ok=True)
            shutil.chown(path=path, user=user)

            instance_uefi_code = path / "uefi_code.fd"
            instance_uefi_code.symlink_to(uefi_code)
            instance_uefi_vars = path / "uefi_vars.fd"
            shutil.copyfile(uefi_vars, instance_uefi_vars)

            os_disk = await DiskEntity.create(
                name="OS Disk 0",
                path=path / "os.qcow2",
                size=os_disk_size,
                disk_format=DiskFormat.QCoW2,
                image=image,
            )

            bootstrap_file = path / "bootstrap.json"
            await bootstrap.render(bootstrap_file=bootstrap_file, kv={"name": name})

            entity = InstanceEntity(
                name=name,
                path=path,
                uefi_code=instance_uefi_code,
                uefi_vars=instance_uefi_vars,
                vcpu=vcpu,
                ram=ram,
                os_disk=os_disk,
                network=network,
                bootstrap=bootstrap,
                bootstrap_file=bootstrap_file,
            )

            outcome = await InstanceEntity.repository.create(entity)
            await task.done(msg="Successfully created")
            return outcome
        except Exception as e:
            if os_disk_size is not None:
                await os_disk.remove()
            await task.fail(msg=f"Some exception {e} occurred")
            shutil.rmtree(path)
            raise InstanceException(status=400, msg=f"Some exception {e}")

    async def modify(self, schema: InstanceModifySchema, task: TaskEntity):
        if schema.state == InstanceState.STARTED:
            await self.start()
        if schema.state == InstanceState.STOPPED:
            await self.stop()
        await task.done(msg="Successfully modified")

    async def start(self):
        self._popen = self.runtime.qemu_service.start(self)
        self._state = InstanceState.STARTED

    async def stop(self):
        if self._popen is None:
            return
        self._popen.terminate()
        self._state = InstanceState.STOPPED

    async def remove(self):
        await self.stop()
        shutil.rmtree(self.path)
        await InstanceEntity.repository.remove(self.uid)


class InstanceRepository(AsyncRepository[InstanceEntity, InstanceModel]):
    pass
