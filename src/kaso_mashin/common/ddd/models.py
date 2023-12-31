from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import Base, EntityModel, BinaryScale


class InstanceModel(EntityModel, Base):
    __tablename__ = 'ddd_instances'

    name: Mapped[str] = mapped_column(String(64), unique=True)
    vcpu: Mapped[int] = mapped_column(Integer)
    ram: Mapped[int] = mapped_column(Integer)


class ImageModel(EntityModel, Base):
    __tablename__ = 'ddd_images'

    name: Mapped[str] = mapped_column(String(64), unique=True)
    min_vcpu: Mapped[int] = mapped_column(Integer, default=0)
    min_ram: Mapped[int] = mapped_column(Integer, default=0)
    min_ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.GB)
    min_disk: Mapped[int] = mapped_column(Integer, default=0)
    min_disk_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.GB)
