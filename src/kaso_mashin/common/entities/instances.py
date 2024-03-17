import pathlib
import shutil
import subprocess
import uuid

from pydantic import Field

from sqlalchemy import String, Integer, Enum, UUID
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntitySchema,
    EntityModel,
    Entity,
    AggregateRoot,
    AsyncRepository,
    BinarySizedValue, BinaryScale
)

from kaso_mashin.common.entities import (
    TaskEntity,
    ImageEntity,
    DiskEntity, DiskFormat, DiskGetSchema,
    NetworkEntity, NetworkGetSchema
)


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
    os_disk_uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'))
    network_uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'))


class InstanceEntity(Entity, AggregateRoot):
    """
    Domain model entity for an instance
    """

    def __init__(self,
                 name: str,
                 path: pathlib.Path,
                 uefi_code: pathlib.Path,
                 uefi_vars: pathlib.Path,
                 vcpu: int,
                 ram: BinarySizedValue,
                 mac: str,
                 os_disk: DiskEntity,
                 network: NetworkEntity):
        super().__init__()
        self._name = name
        self._path = path
        self._uefi_code = uefi_code
        self._uefi_vars = uefi_vars
        self._vcpu = vcpu
        self._ram = ram
        self._mac = mac
        self._os_disk = os_disk
        self._network = network

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

    def __eq__(self, other: 'InstanceEntity') -> bool:
        return all([
            super().__eq__(other),
            self.name == other.name,
            self.path == other.path,
            self.uefi_code == other.uefi_code,
            self.uefi_vars == other.uefi_vars,
            self.vcpu == other.vcpu,
            self.ram == other.ram,
            self.mac == other.mac,
            self.os_disk == other.os_disk,
            self.network == other.network
        ])

    def __repr__(self) -> str:
        return (
            f'<InstanceEntity(uid={self.uid}, '
            f'name={self.name}, '
            f'path={self.path}, '
            f'uefi_code={self.uefi_code}, '
            f'uefi_vars={self.uefi_vars}, '
            f'vcpu={self.vcpu}, '
            f'ram={self.ram}, '
            f'mac={self.mac}, '
            f'os_disk={self.os_disk}, '
            f'network={self.network}'
            ')>'
        )

    @staticmethod
    async def from_model(model: InstanceModel) -> 'InstanceEntity':
        # TODO: Internal consistency. This will fail if the disk is dead
        os_disk = await DiskEntity.repository.get_by_uid(model.os_disk_uid)
        network = await NetworkEntity.repository.get_by_uid(model.network_uid)

        entity = InstanceEntity(name=model.name,
                                path=pathlib.Path(model.path),
                                uefi_code=pathlib.Path(model.uefi_code),
                                uefi_vars=pathlib.Path(model.uefi_vars),
                                vcpu=model.vcpu,
                                ram=BinarySizedValue(value=model.ram, scale=BinaryScale(model.ram_scale)),
                                mac=model.mac,
                                os_disk=os_disk,
                                network=network)
        entity._uid = UniqueIdentifier(model.uid)
        return entity

    async def to_model(self, model: InstanceModel | None = None) -> InstanceModel:
        if model is None:
            return InstanceModel(uid=str(self.uid),
                                 name=self.name,
                                 path=str(self.path),
                                 uefi_code=str(self.uefi_code),
                                 uefi_vars=str(self.uefi_vars),
                                 vcpu=self.vcpu,
                                 ram=self.ram.value,
                                 ram_scale=self.ram.scale,
                                 mac=self.mac,
                                 os_disk_uid=str(self.os_disk.uid),
                                 network_uid=str(self.network.uid))
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
            return model

    @staticmethod
    async def create(task: TaskEntity,
                     user: str,
                     name: str,
                     path: pathlib.Path,
                     uefi_code: pathlib.Path,
                     uefi_vars: pathlib.Path,
                     vcpu: int,
                     ram: BinarySizedValue,
                     image: ImageEntity,
                     os_disk_size: BinarySizedValue,
                     network: NetworkEntity) -> 'InstanceEntity':
        if path.exists():
            raise InstanceException(status=400,
                                    msg=f'Instance path at {path} already exists',
                                    task=task)
        os_disk = None
        try:
            path.mkdir(parents=True, exist_ok=True)
            shutil.chown(path=path, user=user)

            instance_uefi_code = path / 'uefi_code.fd'
            instance_uefi_code.symlink_to(uefi_code)
            instance_uefi_vars = path / 'uefi_vars.fd'
            shutil.copyfile(uefi_vars, instance_uefi_vars)

            os_disk = await DiskEntity.create(name='OS Disk 0',
                                              path=path / 'os.qcow2',
                                              size=os_disk_size,
                                              disk_format=DiskFormat.QCoW2,
                                              image=image)

            entity = InstanceEntity(name=name,
                                    path=path,
                                    uefi_code=instance_uefi_code,
                                    uefi_vars=instance_uefi_vars,
                                    vcpu=vcpu,
                                    ram=ram,
                                    mac=f'005056{uuid.uuid4().hex[:6]}',
                                    os_disk=os_disk,
                                    network=network)

            outcome = await InstanceEntity.repository.create(entity)
            await task.done(msg='Successfully created')
            return outcome
        except Exception as e:
            if os_disk_size is not None:
                await os_disk.remove()
            await task.fail(msg=f'Some exception {e} occurred')
            shutil.rmtree(path)
            raise InstanceException(status=400, msg=f'Some exception {e}')

    async def modify(self, task: TaskEntity):
        await task.done(msg='Successfully modified')

    async def start(self):
        pass

    async def stop(self):
        pass

    async def remove(self):
        shutil.rmtree(self.path)
        await InstanceEntity.repository.remove(self.uid)


class InstanceRepository(AsyncRepository[InstanceEntity, InstanceModel]):
    pass


class InstanceListSchema(EntitySchema):
    """
    Schema to list instances
    """
    uid: UniqueIdentifier = Field(description='The unique identifier of the instance',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The instance name', examples=['k8s-master', 'your-mom'])


class InstanceCreateSchema(EntitySchema):
    """
    Schema to create an instance
    """
    name: str = Field(description='The instance name', examples=['k8s-master', 'your-mom'])
    vcpu: int = Field(description='Number of virtual CPU cores', examples=[2])
    ram: BinarySizedValue = Field(description='Amount of RAM',
                                  examples=[BinarySizedValue(2, BinaryScale.G)])
    image_uid: UniqueIdentifier = Field(description='The image UID from which to create the OS disk from',
                                        examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    os_disk_size: BinarySizedValue = Field(description='Size of the OS disk')
    network_uid: UniqueIdentifier = Field(description='The network on which to run this instance',
                                          examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])


class InstanceGetSchema(EntitySchema):
    """
    Schema to get information about a specific instance
    """
    uid: UniqueIdentifier = Field(description='The unique identifier of the instance',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The instance name', examples=['k8s-master', 'your-mom'])
    uefi_code: pathlib.Path = Field(description='Path to the UEFI code file for this instance')
    uefi_vars: pathlib.Path = Field(description='Path to the UEFI variables file for this instance')
    vcpu: int = Field(description='Number of virtual CPU cores', examples=[2])
    ram: BinarySizedValue = Field(description='Amount of RAM',
                                  examples=[BinarySizedValue(2, BinaryScale.G)])
    mac: str = Field(description='Instance MAC address')
    os_disk: DiskGetSchema = Field(description='The image from which to create the OS disk from')
    network: NetworkGetSchema = Field(description='The network on which to run this instance',
                                      examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])


class InstanceModifySchema(EntitySchema):
    """
    Schema to modify an existing instance
    """
    pass
