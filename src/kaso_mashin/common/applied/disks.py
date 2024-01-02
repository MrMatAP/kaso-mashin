import typing
import uuid
import dataclasses
import pathlib

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import (
    UniqueIdentifier, BinaryScale, KMException,
    AggregateRoot, BinarySizedValue,
    Base, AggregateRootModel, Repository, T_AggregateRoot, T_AggregateRootModel)
from .images import ImageEntity

import os
import subprocess


class DiskException(KMException):
    pass


@dataclasses.dataclass
class DiskEntity(AggregateRoot):
    """
    Domain model entity for a disk
    """
    name: str
    path: pathlib.Path
    id: UniqueIdentifier = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    size: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(value=5, scale=BinaryScale.G))

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


class DiskModel(AggregateRootModel, Base):
    """
    Representation of a disk entity in the database
    """
    __tablename__ = 'disks'
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer, default=0)
    size_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)


class DiskRepository(Repository[DiskEntity, DiskModel]):

    def marshal(self, entity: typing.Type[T_AggregateRoot]) -> T_AggregateRootModel:
        return DiskModel(id=str(entity.id),
                         name=entity.name,
                         path=str(entity.path),
                         size=entity.size.value,
                         size_scale=entity.size.scale)

    def merge(self, update: T_AggregateRoot, model: T_AggregateRootModel) -> T_AggregateRootModel:
        model.name = update.name
        model.path = str(update.path)
        model.size = update.size.value
        model.size_scale = update.size.scale
        return model

    def unmarshal(self, model: T_AggregateRootModel) -> T_AggregateRoot:
        return DiskEntity(id=model.id,
                          name=model.name,
                          path=pathlib.Path(model.path),
                          size=BinarySizedValue(value=model.size, scale=model.size_scale))

