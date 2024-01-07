import dataclasses
import pathlib

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin.common.generics.base_types import Entity, BinarySizedValue, BinaryScale, KasoMashinException, ORMBase, \
    AggregateRoot, T_Entity, UniqueIdentifier


class ImageException(KasoMashinException):
    pass


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

    def merge(self, other: 'ImageModel'):
        self.name = other.name
        self.path = other.path
        self.min_vcpu = other.min_vcpu
        self.min_ram = other.min_ram
        self.min_ram_scale = other.min_ram_scale
        self.min_disk = other.min_disk
        self.min_disk_scale = other.min_disk_scale


@dataclasses.dataclass
class ImageEntity(Entity[ImageModel]):
    """
    Domain model for an image
    """
    name: str = dataclasses.field(default=None)
    path: pathlib.Path = dataclasses.field(default=None)
    min_vcpu: int = dataclasses.field(default=0)
    min_ram: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(0, BinaryScale.G))
    min_disk: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(0, BinaryScale.G))


class ImageAggregateRoot(AggregateRoot[ImageEntity, ImageModel]):

    def validate(self, entity: T_Entity) -> bool:
        return True

    def serialise(self, entity: ImageEntity) -> ImageModel:
        return ImageModel(id=str(entity.id),
                          name=entity.name,
                          path=str(entity.path),
                          min_vcpu=entity.min_vcpu,
                          min_ram=entity.min_ram.value,
                          min_ram_scale=entity.min_ram.scale,
                          min_disk=entity.min_disk.value,
                          min_disk_scale=entity.min_disk.scale)

    def deserialise(self, model: ImageModel) -> ImageEntity:
        return ImageEntity(id=UniqueIdentifier(model.id),
                           name=model.name,
                           path=pathlib.Path(model.path),
                           min_vcpu=model.min_vcpu,
                           min_ram=BinarySizedValue(model.min_ram, BinaryScale(model.min_ram_scale)),
                           min_disk=BinarySizedValue(model.min_disk, BinaryScale(model.min_disk_scale)))
