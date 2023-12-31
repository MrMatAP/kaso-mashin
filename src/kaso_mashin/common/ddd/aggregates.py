import dataclasses
import uuid

from .base_types import UniqueIdentifier, BinaryScale, AggregateRoot, ValueObject
from .models import ImageModel


@dataclasses.dataclass
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

    @staticmethod
    def from_model(model: ImageModel) -> 'ImageEntity':
        return ImageEntity(id=model.id,
                           name=model.name,
                           min_vcpu=model.min_vcpu,
                           min_ram=SizedValue(value=model.min_ram, scale=BinaryScale.GB),
                           min_disk=SizedValue(value=model.min_disk, scale=BinaryScale.GB))

    def as_model(self) -> ImageModel:
        return ImageModel(id=self.id,
                          name=self.name,
                          min_vcpu=self.min_vcpu,
                          min_ram=self.min_ram.value,
                          min_disk=self.min_disk.value)

