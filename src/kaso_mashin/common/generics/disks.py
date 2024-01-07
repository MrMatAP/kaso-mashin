import dataclasses
import os
import pathlib
import subprocess

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin.common.generics.base_types import Entity, BinarySizedValue, BinaryScale, KasoMashinException, ORMBase, \
    AggregateRoot, T_Entity, UniqueIdentifier, AsyncAggregateRoot
from kaso_mashin.common.generics.images import ImageEntity


class DiskException(KasoMashinException):
    pass


class DiskModel(ORMBase):
    """
    Representation of a disk entity in the database
    """
    __tablename__ = 'disks'
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer, default=0)
    size_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)

    def merge(self, other: 'DiskModel'):
        self.name = other.name
        self.path = other.path
        self.size = other.size
        self.size_scale = other.size_scale


@dataclasses.dataclass
class DiskEntity(Entity[DiskModel]):
    """
    Domain model entity for a disk
    """
    name: str = dataclasses.field(default=None)
    path: pathlib.Path = dataclasses.field(default=None)
    size: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(5, BinaryScale.G))

    @staticmethod
    def create(name: str, path: pathlib.Path, size: BinarySizedValue) -> 'DiskEntity':
        if path.exists():
            raise DiskException(code=400, msg=f'Disk at {path} already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        disk = DiskEntity(name=name, path=path, size=size)
        try:
            subprocess.run(['/opt/homebrew/bin/qemu-img',
                            'create',
                            '-f', 'raw',
                            disk.path,
                            str(size)],
                           check=True)
        except subprocess.CalledProcessError as e:
            raise DiskException(code=500, msg=f'Failed to create disk: {e.output}') from e
        return disk

    @staticmethod
    def create_from_image(name: str, path: pathlib.Path, size: BinarySizedValue, image: ImageEntity):
        if path.exists():
            raise DiskException(code=400, msg=f'Disk at {path} already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        disk = DiskEntity(name=name, path=path, size=size)
        try:
            subprocess.run(['/opt/homebrew/bin/qemu-img',
                            'create',
                            '-f', 'qcow2',
                            '-F', 'qcow2',
                            '-b', image.path,
                            '-o', 'compat=v3',
                            disk.path,
                            str(size)],
                           check=True)
        except subprocess.CalledProcessError as e:
            raise DiskException(code=500, msg=f'Failed to create disk from image: {e.output}') from e
        return disk

    def resize(self, new_size: BinarySizedValue):
        try:
            subprocess.run(['/opt/homebrew/bin/qemu-img',
                            'resize',
                            self.path,
                            str(new_size)],
                           check=True)
            self.size = new_size
        except subprocess.CalledProcessError as e:
            raise DiskException(code=500, msg=f'Failed to resize disk: {e.output}') from e

    def remove(self):
        if not self.path.exists():
            return
        os.unlink(self.path)


class DiskAggregateRoot(AggregateRoot[DiskEntity, DiskModel]):

    def validate(self, entity: T_Entity) -> bool:
        return True

    def serialise(self, entity: DiskEntity) -> DiskModel:
        return DiskModel(id=str(entity.id),
                         name=entity.name,
                         path=str(entity.path),
                         size=entity.size.value,
                         size_scale=entity.size.scale)

    def deserialise(self, model: DiskModel) -> DiskEntity:
        return DiskEntity(id=UniqueIdentifier(model.id),
                          name=model.name,
                          path=pathlib.Path(model.path),
                          size=BinarySizedValue(model.size, BinaryScale(model.size_scale)))


class AsyncDiskAggregateRoot(AsyncAggregateRoot[DiskEntity, DiskModel]):

    def validate(self, entity: T_Entity) -> bool:
        return True

    def serialise(self, entity: DiskEntity) -> DiskModel:
        return DiskModel(id=str(entity.id),
                         name=entity.name,
                         path=str(entity.path),
                         size=entity.size.value,
                         size_scale=entity.size.scale)

    def deserialise(self, model: DiskModel) -> DiskEntity:
        return DiskEntity(id=UniqueIdentifier(model.id),
                          name=model.name,
                          path=pathlib.Path(model.path),
                          size=BinarySizedValue(model.size, BinaryScale(model.size_scale)))
