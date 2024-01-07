import dataclasses
import pathlib
import os
import subprocess

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import (
    KasoMashinException,
    ORMBase,
    UniqueIdentifier,
    BinaryScale, BinarySizedValue,
    AggregateRoot
)
from .images import ImageEntity


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

    def update(self, other: 'DiskModel'):
        self.name = other.name
        self.path = other.path
        self.size = other.size
        self.size_scale = other.size_scale


@dataclasses.dataclass
class DiskEntity(AggregateRoot[DiskModel]):
    """
    Domain model entity for a disk
    """
    name: str = dataclasses.field(default=None)
    path: pathlib.Path = dataclasses.field(default=None)
    size: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(5, BinaryScale.G))

    def serialise(self) -> DiskModel:
        return DiskModel(id=str(self.id),
                         name=self.name,
                         path=str(self.path),
                         size=self.size.value,
                         size_scale=self.size.scale)

    @staticmethod
    def deserialise(model: DiskModel) -> 'DiskEntity':
        return DiskEntity(id=UniqueIdentifier(model.id),
                          name=model.name,
                          path=pathlib.Path(model.path),
                          size=BinarySizedValue(value=model.size, scale=BinaryScale(model.size_scale)))

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
