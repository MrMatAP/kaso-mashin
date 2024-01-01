from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import Base, EntityModel, BinaryScale
from .aggregates import InstanceEntity, ImageEntity, SizedValue


class InstanceModel(EntityModel, Base):
    __tablename__ = 'ddd_instances'

    name: Mapped[str] = mapped_column(String(64), unique=True)
    vcpu: Mapped[int] = mapped_column(Integer)
    ram: Mapped[int] = mapped_column(Integer)
    ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale))

    @staticmethod
    def from_aggregateroot(entity: InstanceEntity) -> 'InstanceModel':
        return InstanceModel(id=entity.id,
                             name=entity.name,
                             vcpu=entity.vcpu,
                             ram=entity.ram.value,
                             ram_scale=entity.ram.scale)

    def as_entity(self) -> InstanceEntity:
        return InstanceEntity(id=self.id,
                              name=self.name,
                              vcpu=self.vcpu,
                              ram=SizedValue(value=self.ram, scale=self.ram_scale))


class ImageModel(EntityModel, Base):
    __tablename__ = 'ddd_images'

    name: Mapped[str] = mapped_column(String(64), unique=True)
    min_vcpu: Mapped[int] = mapped_column(Integer, default=0)
    min_ram: Mapped[int] = mapped_column(Integer, default=0)
    min_ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.GB)
    min_disk: Mapped[int] = mapped_column(Integer, default=0)
    min_disk_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.GB)

    @staticmethod
    def from_aggregateroot(entity: ImageEntity) -> 'ImageModel':
        return ImageModel(id=entity.id,
                          name=entity.name,
                          min_vcpu=entity.min_vcpu,
                          min_ram=entity.min_ram.value,
                          min_ram_scale=entity.min_ram.scale,
                          min_disk=entity.min_disk.value,
                          min_disk_scale=entity.min_disk.scale)

    def as_entity(self) -> ImageEntity:
        return ImageEntity(id=self.id,
                           name=self.name,
                           min_vcpu=self.min_vcpu,
                           min_ram=SizedValue(value=self.min_ram, scale=self.min_ram_scale),
                           min_disk=SizedValue(value=self.min_disk, scale=self.min_disk_scale))
