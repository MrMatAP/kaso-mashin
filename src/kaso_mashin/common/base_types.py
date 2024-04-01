"""
Common Base Types
"""
import dataclasses
import enum

import pydantic
from pydantic import Field

from .ddd_scaffold import (
    ValueObject,
    EntitySchema
)


class BinaryScale(enum.StrEnum):
    k = 'Kilobytes'
    M = 'Megabytes'
    G = 'Gigabytes'
    T = 'Terabytes'
    P = 'Petabytes'
    E = 'Exabytes'


class BinarySizedValueSchema(EntitySchema):
    value: int = Field(description="The value", examples=[2, 4, 8])
    scale: BinaryScale = Field(description="The binary scale", examples=[BinaryScale.M, BinaryScale.G, BinaryScale.T])


@dataclasses.dataclass(frozen=True)
class BinarySizedValue(ValueObject):
    """
    A sized binary value object
    """
    value: int = dataclasses.field(default=0)
    scale: BinaryScale = dataclasses.field(default=BinaryScale.G)

    def __str__(self):
        return f'{self.value}{self.scale.name}'

    def __repr__(self):
        return f'<BinarySizedValue(value={self.value}, scale={self.scale.name})>'

    def __lt__(self, other: 'BinarySizedValue') -> bool:
        if any([
            self.scale == other.scale and self.value < other.value,
            self.scale == BinaryScale.E and other.scale in [BinaryScale.P, BinaryScale.T, BinaryScale.G, BinaryScale.M, BinaryScale.k],
            self.scale == BinaryScale.P and other.scale in [BinaryScale.T, BinaryScale.G, BinaryScale.M, BinaryScale.k],
            self.scale == BinaryScale.T and other.scale in [BinaryScale.G, BinaryScale.M, BinaryScale.k],
            self.scale == BinaryScale.G and other.scale in [BinaryScale.M, BinaryScale.k],
            self.scale == BinaryScale.M and other.scale == BinaryScale.k
        ]):
            return True
        return False

    def __gt__(self, other: 'BinarySizedValue') -> bool:
        return not self.__lt__(other)


class ExceptionSchema(pydantic.BaseModel):
    """
    Schema for an exception
    """
    status: int = pydantic.Field(description='The exception status code', default=500)
    msg: str = pydantic.Field(description='A user-readable error description')

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'status': 400,
                    'msg': 'I did not like your input, at all'
                }
            ]
        }
    }
