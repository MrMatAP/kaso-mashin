import typing
import uuid
import dataclasses
import pathlib

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base_types import (
    UniqueIdentifier, BinaryScale,
    AggregateRoot, BinarySizedValue,
    Base, AggregateRootModel, Repository, T_AggregateRoot, T_AggregateRootModel)


@dataclasses.dataclass
class DiskEntity(AggregateRoot):
    """
    Domain model entity for a disk
    """
    name: str
    path: pathlib.Path
    id: UniqueIdentifier = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    size: BinarySizedValue = dataclasses.field(default_factory=lambda: BinarySizedValue(value=5, scale=BinaryScale.GB))
    

class DiskModel(AggregateRootModel, Base):
    """
    Representation of a disk entity in the database
    """
    __tablename__ = 'disks'
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer, default=0)
    size_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.GB)


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

