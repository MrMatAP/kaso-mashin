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
    b = 'Bytes'
    k = 'Kilobytes'
    M = 'Megabytes'
    G = 'Gigabytes'
    T = 'Terabytes'
    P = 'Petabytes'
    E = 'Exabytes'

    @staticmethod
    def scale_value(scale: 'BinaryScale') -> int:
        return {
            BinaryScale.b: 0,
            BinaryScale.k: 1,
            BinaryScale.M: 2,
            BinaryScale.G: 3,
            BinaryScale.T: 4,
            BinaryScale.P: 5,
            BinaryScale.E: 6
        }[scale]

    def __lt__(self, other: 'BinaryScale') -> bool:
        return BinaryScale.scale_value(self) < BinaryScale.scale_value(other)

    def __gt__(self, other: 'BinaryScale') -> bool:
        return BinaryScale.scale_value(self) > BinaryScale.scale_value(other)


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

    def at_scale(self, scale: BinaryScale = BinaryScale.M) -> 'BinarySizedValue':
        if self.scale == scale:
            return self
        scale_difference = BinaryScale.scale_value(self.scale) - BinaryScale.scale_value(scale)
        if scale_difference == 0:
            return self
        if scale_difference > 0:
            return BinarySizedValue(scale=scale,
                                    value=int(self.value * (1024 ** scale_difference)))
        return BinarySizedValue(scale=scale,
                                value=int(self.value / (1024 ** abs(scale_difference))))

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
