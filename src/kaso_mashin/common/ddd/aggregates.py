import dataclasses
import uuid
import pathlib

from .base_types import UniqueIdentifier, BinaryScale, Aggregate, AggregateRoot, ValueObject


@dataclasses.dataclass(frozen=True)
class SizedValue(ValueObject):
    value: int = dataclasses.field(default=0)
    scale: BinaryScale = dataclasses.field(default=BinaryScale.GB)


@dataclasses.dataclass
class ImageEntity(AggregateRoot):
    name: str
    id: UniqueIdentifier = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    min_vcpu: int = dataclasses.field(default=0)
    min_ram: SizedValue = dataclasses.field(default_factory=lambda: SizedValue(value=0, scale=BinaryScale.GB))
    min_disk: SizedValue = dataclasses.field(default_factory=lambda: SizedValue(value=0, scale=BinaryScale.GB))


@dataclasses.dataclass
class DiskEntity(Aggregate):
    name: str
    path: pathlib.Path
    id: UniqueIdentifier = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    size: SizedValue = dataclasses.field(default_factory=lambda: SizedValue(value=5, scale=BinaryScale.GB))


@dataclasses.dataclass(frozen=True)
class InstanceEntity(AggregateRoot):
    name: str
    # os_disk: DiskEntity
    id: UniqueIdentifier = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    vcpu: int = dataclasses.field(default=1)
    ram: SizedValue = dataclasses.field(default_factory=lambda: SizedValue(value=2, scale=BinaryScale.GB))

