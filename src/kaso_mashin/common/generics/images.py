import dataclasses
import pathlib

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import (
    KasoMashinException,
    ORMBase,
    UniqueIdentifier,
    BinaryScale, BinarySizedValue,
    AggregateRoot, T_AggregateRootModel
)


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

    def update(self, other: 'ImageModel'):
        self.name = other.name
        self.path = other.path
        self.min_vcpu = other.min_vcpu
        self.min_ram = other.min_ram
        self.min_ram_scale = other.min_ram_scale
        self.min_disk = other.min_disk
        self.min_disk_scale = other.min_disk_scale


@dataclasses.dataclass
class ImageEntity(AggregateRoot[ImageModel]):
    """
    Domain model for an image
    """
    name: str
    path: pathlib.Path
    min_vcpu: int = dataclasses.field(default=0)
    min_ram: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(0, BinaryScale.G))
    min_disk: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(0, BinaryScale.G))

    def serialise(self) -> ImageModel:
        return ImageModel(id=str(self.id),
                          name=self.name,
                          path=str(self.path),
                          min_vcpu=self.min_vcpu,
                          min_ram=self.min_ram.value,
                          min_ram_scale=self.min_ram.scale,
                          min_disk=self.min_disk.value,
                          min_disk_scale=self.min_disk.scale)

    @staticmethod
    def deserialise(model: ImageModel) -> 'ImageEntity':
        return ImageEntity(id=UniqueIdentifier(model.id),
                           name=model.name,
                           path=pathlib.Path(model.path),
                           min_vcpu=model.min_vcpu,
                           min_ram=BinarySizedValue(model.min_ram, BinaryScale(model.min_ram_scale)),
                           min_disk=BinarySizedValue(model.min_disk, BinaryScale(model.min_disk_scale)))
