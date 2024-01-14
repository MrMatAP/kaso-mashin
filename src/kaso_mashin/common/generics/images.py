import dataclasses
import subprocess
import pathlib
import typing
import uuid

from sqlalchemy import String, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kaso_mashin.common.base_types import (
    KasoMashinException,
    ORMBase,
    Entity, AggregateRoot, ValueObject,
    BinarySizedValue,
    UniqueIdentifier, BinaryScale, DiskFormat)


class ImageException(KasoMashinException):
    pass


class OSDiskModel(ORMBase):
    __tablename__ = 'os_disks'
    path: Mapped[str] = mapped_column(String())
    image_id: Mapped[str] = mapped_column(ForeignKey("images.uid"))

    def merge(self, other: 'OSDiskModel'):
        self.path = other.path
        self.image_id = other.image_id


@dataclasses.dataclass(frozen=True)
class OSDiskValueObject(ValueObject):
    path: pathlib.Path
    image_id: UniqueIdentifier


class ImageModel(ORMBase):
    """
    Representation of an image entity in the database
    """
    __tablename__ = 'images'
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    min_vcpu: Mapped[int] = mapped_column(Integer, default=0)
    min_ram: Mapped[int] = mapped_column(Integer, default=0)
    min_ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    min_disk: Mapped[int] = mapped_column(Integer, default=0)
    min_disk_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    os_disks: Mapped[typing.List[OSDiskModel]] = relationship()

    def merge(self, other: 'ImageModel'):
        self.name = other.name
        self.path = other.path
        self.min_vcpu = other.min_vcpu
        self.min_ram = other.min_ram
        self.min_ram_scale = other.min_ram_scale
        self.min_disk = other.min_disk
        self.min_disk_scale = other.min_disk_scale


class ImageEntity(Entity):
    """
    Domain model for an image
    """

    def __init__(self,
                 owner: 'AggregateRoot',
                 name: str,
                 path: pathlib.Path,
                 min_vcpu: int = 0,
                 min_ram: BinarySizedValue = BinarySizedValue(0, BinaryScale.G),
                 min_disk: BinarySizedValue = BinarySizedValue(0, BinaryScale.G),
                 os_disks: typing.List[OSDiskValueObject] | None = None,
                 uid: UniqueIdentifier = uuid.uuid4()) -> None:
        super().__init__(owner, uid)
        self._name = name
        self._path = path
        self._min_vcpu = min_vcpu
        self._min_ram = min_ram
        self._min_disk = min_disk
        self._os_disks = os_disks or []
        self._downloaded = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def min_vcpu(self) -> int:
        return self._min_vcpu

    @property
    def min_ram(self) -> BinarySizedValue:
        return self._min_ram

    @property
    def min_disk(self) -> BinarySizedValue:
        return self._min_disk

    @property
    def os_disks(self) -> typing.List[OSDiskValueObject]:
        return self._os_disks

    def __eq__(self, other: 'ImageEntity') -> bool:     # type: ignore[override]
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._path == other.path,
            self._min_vcpu == other.min_vcpu,
            self._min_ram == other.min_ram,
            self._min_disk == other.min_disk])

    @staticmethod
    async def create(owner: 'AggregateRoot',
                     name: str,
                     path: pathlib.Path,
                     min_vcpu: int = 0,
                     min_ram: BinarySizedValue = BinarySizedValue(0, BinaryScale.G),
                     min_disk: BinarySizedValue = BinarySizedValue(0, BinaryScale.G)) -> 'ImageEntity':
        if path.exists():
            raise ImageException(code=400, msg=f'Image at {path} already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            image = ImageEntity(owner=owner,
                                name=name,
                                path=path,
                                min_vcpu=min_vcpu,
                                min_ram=min_ram,
                                min_disk=min_disk)
            return await owner.create(image)
        finally:
            pass

    async def create_os_disk(self, path: pathlib.Path, size: BinarySizedValue):
        if path.exists():
            raise ImageException(code=400, msg=f'OS Disk at {path} already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(['/opt/homebrew/bin/qemu-img',
                            'create',
                            '-f', str(DiskFormat.QCoW2),
                            '-F', str(DiskFormat.QCoW2),
                            '-b', str(path),
                            '-o', 'compat=v3',
                            path,
                            str(size)],
                           check=True)
            self.os_disks.append(OSDiskValueObject(path=path, image_id=self.uid))
            return await self._owner.modify(self)
        except subprocess.CalledProcessError as e:
            path.unlink(missing_ok=True)
            raise ImageException(code=500, msg=f'Failed to create OS disk from image: {e.output}') from e

    async def remove(self):
        self.path.unlink(missing_ok=True)
        await self._owner.remove(self.uid)

    async def set_min_vcpu(self, value: int):
        self._min_vcpu = value
        await self._owner.modify(self)

    async def set_min_ram(self, value: BinarySizedValue):
        self._min_ram = value
        await self._owner.modify(self)

    async def set_min_disk(self, value: BinarySizedValue):
        self._min_disk = value
        await self._owner.modify(self)


class ImageAggregateRoot(AggregateRoot[ImageEntity, ImageModel]):

    async def _to_model(self, entity: ImageEntity) -> ImageModel:
        os_disks = [OSDiskModel(path=d.path, image_id=d.image_id) for d in entity.os_disks]
        return ImageModel(uid=str(entity.uid),
                          name=entity.name,
                          path=str(entity.path),
                          min_vcpu=entity.min_vcpu,
                          min_ram=entity.min_ram.value,
                          min_ram_scale=entity.min_ram.scale,
                          min_disk=entity.min_disk.value,
                          min_disk_scale=entity.min_disk.scale,
                          os_disks=os_disks)

    async def _from_model(self, model: ImageModel) -> ImageEntity:
        return ImageEntity(owner=self,
                           uid=UniqueIdentifier(model.uid),
                           name=model.name,
                           path=pathlib.Path(model.path),
                           min_vcpu=model.min_vcpu,
                           min_ram=BinarySizedValue(model.min_ram, BinaryScale(model.min_ram_scale)),
                           min_disk=BinarySizedValue(model.min_disk, BinaryScale(model.min_disk_scale)),
                           os_disks=[OSDiskValueObject(path=pathlib.Path(d.path),
                                                       image_id=UniqueIdentifier(d.image_id))
                                     for d in model.os_disks])
