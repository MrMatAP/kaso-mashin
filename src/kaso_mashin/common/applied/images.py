import uuid
import dataclasses
import pathlib

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import (
    UniqueIdentifier, BinaryScale, BinarySizedValue,
    T_AggregateRoot, AggregateRoot,
    T_AggregateRootModel, AggregateRootModel,
    Base, Repository)


@dataclasses.dataclass
class ImageEntity(AggregateRoot):
    """
    Domain model for an image
    """
    name: str
    path: pathlib.Path
    id: UniqueIdentifier = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    min_vcpu: int = dataclasses.field(default=0)
    min_ram: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(0, BinaryScale.G))
    min_disk: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(0, BinaryScale.G))


class ImageModel(AggregateRootModel, Base):
    """
    Representation of an image entity in the database
    """
    __tablename__ = 'images'
    name: Mapped[str] = mapped_column(String(64), unique=True)
    path: Mapped[str] = mapped_column(String())
    min_vcpu: Mapped[int] = mapped_column(Integer, default=0)
    min_ram: Mapped[int] = mapped_column(Integer, default=0)
    min_ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    min_disk: Mapped[int] = mapped_column(Integer, default=0)
    min_disk_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)


class ImageRepository(Repository[ImageEntity, ImageModel]):

    def marshal(self, entity: T_AggregateRoot) -> T_AggregateRootModel:
        return ImageModel(id=str(entity.id),
                          name=entity.name,
                          path=str(entity.path),
                          min_vcpu=entity.min_vcpu,
                          min_ram=entity.min_ram.value,
                          min_ram_scale=entity.min_ram.scale,
                          min_disk=entity.min_disk.value,
                          min_disk_scale=entity.min_disk.scale)

    def merge(self, update: T_AggregateRoot, model: T_AggregateRootModel) -> T_AggregateRootModel:
        model.name = update.name
        model.path = str(update.path)
        model.min_vcpu = update.min_vcpu
        model.min_ram = update.min_ram.value
        model.min_ram_scale = update.min_ram.scale
        model.min_disk = update.min_disk.value
        model.min_disk_scale = update.min_disk.scale
        return model

    def unmarshal(self, model: T_AggregateRootModel) -> T_AggregateRoot:
        return ImageEntity(id=model.id,
                           name=model.name,
                           path=pathlib.Path(model.path),
                           min_vcpu=model.min_vcpu,
                           min_ram=BinarySizedValue(model.min_ram, model.min_ram_scale),
                           min_disk=BinarySizedValue(model.min_disk, model.min_disk_scale))
