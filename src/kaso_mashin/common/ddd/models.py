from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import Base, EntityModel


class InstanceModel(EntityModel, Base):
    __tablename__ = 'ddd_instances'

    name: Mapped[str] = mapped_column(String(64), unique=True)
    vcpu: Mapped[int] = mapped_column(Integer)
    ram: Mapped[int] = mapped_column(Integer)


class ImageModel(EntityModel, Base):
    __tablename__ = 'ddd_images'

    name: Mapped[str] = mapped_column(String(64), unique=True)
