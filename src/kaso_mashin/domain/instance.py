import enum
import pathlib
import re
import shutil
import typing

import rich.box
import rich.table

from pydantic import Field
from sqlalchemy import String, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

import kaso_mashin
import kaso_mashin.base
import kaso_mashin.domain.bootstrap
import kaso_mashin.domain.image
import kaso_mashin.domain.disk
import kaso_mashin.domain.network
import kaso_mashin.domain.bootstrap

from kaso_mashin.services import Task


class InstanceException(kaso_mashin.base.KasoMashinException):
    """
    Exception for instance-related issues
    """
    pass


class InstanceState(str, enum.Enum):
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    STARTED = "STARTED"


class InstanceModel(kaso_mashin.base.Model):
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
    ram_scale: Mapped[str] = mapped_column(Enum(kaso_mashin.base.BinaryScale),
                                           default=kaso_mashin.base.BinaryScale.G)
    mac: Mapped[str] = mapped_column(String)
    bootstrap_file: Mapped[str] = mapped_column(String)

    network_uid: Mapped[str] = mapped_column(ForeignKey("networks.uid"))
    network: Mapped['kaso_mashin.domain.network.NetworkModel'] = relationship(lazy='selectin', back_populates='instances')
    disk_uid: Mapped[str] = mapped_column(ForeignKey("disks.uid"))
    disk: Mapped['kaso_mashin.domain.disk.DiskModel'] = relationship(lazy='selectin', back_populates='instance')
    bootstrap_uid: Mapped[str] = mapped_column(ForeignKey("bootstraps.uid"))
    bootstrap: Mapped['kaso_mashin.domain.bootstrap.BootstrapModel'] = relationship(lazy='selectin', back_populates='instances')


class Instance(kaso_mashin.base.AggregateRoot['InstanceRepository']):
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
            ram: kaso_mashin.base.BinarySizedValue,
            image: 'kaso_mashin.domain.image.Image',
            disk: 'kaso_mashin.domain.disk.Disk',
            network: 'kaso_mashin.domain.network.Network',
            bootstrap: 'kaso_mashin.domain.bootstrap.Bootstrap',
            bootstrap_file: pathlib.Path,
    ):
        super().__init__(name)
        self._path = path
        self._uefi_code = uefi_code
        self._uefi_vars = uefi_vars
        self._vcpu = vcpu
        self._ram = ram
        self._mac = self._generate_mac()
        self._image = image
        self._disk = disk
        self._network = network
        self._bootstrap = bootstrap
        self._bootstrap_file = bootstrap_file
        self._popen = None
        self._state = InstanceState.STOPPED

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def vcpu(self) -> int:
        return self._vcpu

    @property
    def ram(self) -> kaso_mashin.base.BinarySizedValue:
        return self._ram

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def image_uid(self) -> kaso_mashin.base.UniqueIdentifier:
        return self._image.uid

    @property
    def os_disk_uid(self) -> kaso_mashin.base.UniqueIdentifier:
        return self._disk.uid

    @property
    def os_disk_size(self) -> kaso_mashin.base.BinarySizedValue:
        return self._disk.size

    @property
    def network_uid(self) -> kaso_mashin.base.UniqueIdentifier:
        return self._network.uid

    @property
    def bootstrap_uid(self) -> kaso_mashin.base.UniqueIdentifier:
        return self._bootstrap.uid

    @property
    def bootstrap_file(self) -> pathlib.Path:
        return self._bootstrap_file

    @property
    def state(self) -> InstanceState:
        return self._state

    # TODO: Consider replacing this in favour of image_uid
    @property
    def image(self) -> 'kaso_mashin.domain.image.Image':
        return self._image

    # TODO: Consider replacing this in favour of os_disk_uid
    @property
    def disk(self) -> 'kaso_mashin.domain.disk.Disk':
        return self._disk

    # TODO: Consider replacing this in favour of network_uid
    @property
    def network(self) -> 'kaso_mashin.domain.network.Network':
        return self._network

    # TODO: Consider replacing this in favour of bootstrap_uid
    @property
    def bootstrap(self) -> 'kaso_mashin.domain.bootstrap.Bootstrap':
        return self._bootstrap

    # TODO: Consider moving this into bootstrap
    @property
    def uefi_code(self) -> pathlib.Path:
        return self._uefi_code

    # TODO: Consider moving this into bootstrap
    @property
    def uefi_vars(self) -> pathlib.Path:
        return self._uefi_vars

    def __eq__(self, other: "Instance") -> bool:
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
                self.image == other.image,
                self.disk == other.disk,
                self.network == other.network,
                self.bootstrap == other.bootstrap,
                self.bootstrap_file == other.bootstrap_file,
            ]
        )

    @staticmethod
    async def from_model(model: InstanceModel) -> "Instance":
        # TODO: Internal consistency. This will fail if the disk is dead
        image = await kaso_mashin.domain.Image.repository.get_by_uid(kaso_mashin.base.UniqueIdentifier(model.image_uid))
        disk = await kaso_mashin.domain.Disk.repository.get_by_uid(kaso_mashin.base.UniqueIdentifier(model.disk_uid))
        network = await kaso_mashin.domain.Network.repository.get_by_uid(kaso_mashin.base.UniqueIdentifier(model.network_uid))
        bootstrap = await kaso_mashin.domain.Bootstrap.repository.get_by_uid(
            kaso_mashin.base.UniqueIdentifier(model.bootstrap_uid)
        )

        entity = Instance(
            name=model.name,
            path=pathlib.Path(model.path),
            uefi_code=pathlib.Path(model.uefi_code),
            uefi_vars=pathlib.Path(model.uefi_vars),
            vcpu=model.vcpu,
            ram=kaso_mashin.base.BinarySizedValue(value=model.ram, scale=kaso_mashin.base.BinaryScale(model.ram_scale)),
            image=image,
            disk=disk,
            network=network,
            bootstrap=bootstrap,
            bootstrap_file=pathlib.Path(model.bootstrap_file),
        )
        entity._uid = kaso_mashin.base.UniqueIdentifier(model.uid)
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
                image_uid=str(self.image_uid),
                disk_uid=str(self.disk.uid),
                network_uid=str(self.network_uid),
                bootstrap_uid=str(self.bootstrap_uid),
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
            model.os_disk_uid = str(self.os_disk_uid)
            model.network_uid = str(self.network_uid)
            model.bootstrap_uid = str(self.bootstrap_uid)
            model.bootstrap_file = str(self.bootstrap_file)
            return model

    def _generate_mac(self) -> str:
        octets = re.findall("..", self.uid.hex[:6])
        return f'{DEFAULT_MAC_PREFIX}:{":".join(octets)}'

    @staticmethod
    async def create(
            task: Task,
            user: str,
            name: str,
            path: pathlib.Path,
            uefi_code: pathlib.Path,
            uefi_vars: pathlib.Path,
            vcpu: int,
            ram: kaso_mashin.base.BinarySizedValue,
            image: 'kaso_mashin.domain.image.Image',
            os_disk_size: kaso_mashin.base.BinarySizedValue,
            network: 'kaso_mashin.domain.network.Network',
            bootstrap: 'kaso_mashin.domain.bootstrap.Bootstrap',
    ) -> "Instance":
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

            disk = await kaso_mashin.domain.disk.Disk.create(
                name="OS Disk 0",
                path=path / "os.qcow2",
                size=os_disk_size,
                disk_format=kaso_mashin.domain.DiskFormat.QCoW2,
                image=image,
            )

            bootstrap_file = path / "bootstrap.json"
            await bootstrap.render(bootstrap_file=bootstrap_file, kv={"name": name})

            entity = Instance(
                name=name,
                path=path,
                uefi_code=instance_uefi_code,
                uefi_vars=instance_uefi_vars,
                vcpu=vcpu,
                ram=ram,
                image=image,
                disk=disk,
                network=network,
                bootstrap=bootstrap,
                bootstrap_file=bootstrap_file,
            )

            outcome = await Instance.repository.create(entity)
            await task.done(msg="Successfully created", outcome=outcome.uid)
            return outcome
        except Exception as e:
            if os_disk_size is not None:
                await disk.remove()
            await task.fail(msg=f"Some exception {e} occurred")
            shutil.rmtree(path)
            raise InstanceException(status=400, msg=f"Some exception {e}")

    # TODO
    # async def modify(self, schema: InstanceModifySchema, task: Task):
    #     if schema.state == InstanceState.STARTED:
    #         await self.start()
    #     if schema.state == InstanceState.STOPPED:
    #         await self.stop()
    #     await task.done(msg="Successfully modified")

    async def start(self):
        try:
            self._popen = self.runtime.qemu_service.start_instance(self)
            self._state = InstanceState.STARTED
        except Exception as e:
            pass

    async def stop(self):
        if self._popen is None:
            return
        self._popen.terminate()
        self._state = InstanceState.STOPPED

    async def remove(self):
        await self.stop()
        shutil.rmtree(self.path)
        await Instance.repository.remove(self)


class InstanceRepository(kaso_mashin.base.Repository[Instance, InstanceModel]):
    """
    A repository of instances
    """
    entity_class = Instance
    model_class = InstanceModel

    @classmethod
    async def from_model(cls, model: InstanceModel, *args, **kwargs) -> Instance:
        kwargs['path'] = pathlib.Path(model.path)
        kwargs['uefi_code'] = model.uefi_code
        kwargs['uefi_vars'] = model.uefi_vars
        return await super().from_model(model, *args, **kwargs)

    @classmethod
    async def to_model(cls, entity: Instance, persisted: InstanceModel | None = None) -> InstanceModel:
        pass


DEFAULT_MAC_PREFIX = "00:50:56"


class InstanceCreateSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to create an instance
    """

    name: str = Field(description="The instance name", examples=["k8s-master", "your-mom"])
    vcpu: int = Field(description="Number of virtual CPU cores", examples=[2])
    ram: kaso_mashin.base.BinarySizedValue = Field(
        description="Amount of RAM",
        examples=[kaso_mashin.base.BinarySizedValue(value=2, scale=kaso_mashin.base.BinaryScale.G)],
    )
    os_disk_size: kaso_mashin.base.BinarySizedValue = Field(description="Size of the OS disk")
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


class InstanceGetSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to get information about a specific instance
    """

    uid: kaso_mashin.base.UniqueIdentifier = Field(
        description="The unique identifier of the instance",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="The instance name", examples=["k8s-master", "your-mom"])
    path: pathlib.Path = Field(description="Path of the instance on the local disk")
    vcpu: int = Field(description="Number of virtual CPU cores", examples=[2])
    ram: kaso_mashin.base.BinarySizedValue = Field(
        description="Amount of RAM",
        examples=[kaso_mashin.base.BinarySizedValue(value=2, scale=kaso_mashin.base.BinaryScale.G)],
    )
    mac: str = Field(description="Instance MAC address")
    network_uid: kaso_mashin.base.UniqueIdentifier = Field(
        description="The network UID on which to run this instance"
    )
    image_uid: kaso_mashin.base.UniqueIdentifier = Field(description="The image UID")
    os_disk_uid: kaso_mashin.base.UniqueIdentifier = Field(description="The OS disk UID")
    os_disk_size: kaso_mashin.base.BinarySizedValue = Field(description="Size of the OS disk")
    bootstrap_uid: kaso_mashin.base.UniqueIdentifier = Field(description="The bootstrapper uid")
    bootstrap_file: pathlib.Path = Field(
        description="The path to the bootstrap file on the local disk"
    )
    state: InstanceState = Field(
        description="The instance state",
        examples=[InstanceState.STOPPED, InstanceState.STARTED],
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
        table.add_row("[blue]Network UID", str(self.network_uid))
        table.add_row("[blue]Image UID", str(self.image_uid))
        table.add_row("[blue]OS Disk UID", str(self.os_disk_uid))
        table.add_row("[blue]Bootstrap UID", str(self.bootstrap_uid))
        table.add_row("[blue]Bootstrap File", str(self.bootstrap_file))
        table.add_row("[blue]State", str(self.state))
        return table


class InstanceListSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to list instances
    """

    entries: typing.List[InstanceGetSchema] = Field(
        description="List of instances", default_factory=list
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Name")
        table.add_column("[blue]State")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name, str(entry.state))
        return table


class InstanceModifySchema(kaso_mashin.base.EntitySchema):
    """
    Schema to modify an existing instance
    """

    state: typing.Optional[InstanceState] = Field(description="The state of the instance")
