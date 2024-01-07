"""
Common Base Types
"""
import abc
import dataclasses
import enum
import typing
import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class KasoMashinException(Exception):

    def __init__(self, code: int, msg: str) -> None:
        super().__init__()
        self._code = code
        self._msg = msg

    def __str__(self) -> str:
        return f'[{self._code}] {self._msg}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(code={self._code}, msg={self._msg})'


class EntityNotFoundException(KasoMashinException):
    pass


class ORMBase(DeclarativeBase):
    """
    ORM base class for persisted entities
    """
    id: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'), primary_key=True)

    @abc.abstractmethod
    def update(self, other: typing.Self):
        pass


UniqueIdentifier = uuid.UUID
T_AggregateRootModel = typing.TypeVar('T_AggregateRootModel', bound=ORMBase)


@dataclasses.dataclass
class Entity(abc.ABC):
    """
    A domain entity
    """
    id: UniqueIdentifier


T_Entity = typing.TypeVar("T_Entity", bound=Entity)


class ValueObject(abc.ABC):
    """
    A domain value object
    """
    pass


@dataclasses.dataclass
class AggregateRoot(Entity, typing.Generic[T_AggregateRootModel]):

    @abc.abstractmethod
    def serialise(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def deserialise(model: 'T_AggregateRootModel'):
        pass


T_AggregateRoot = typing.TypeVar('T_AggregateRoot', bound=AggregateRoot)


class BinaryScale(enum.StrEnum):
    k = 'Kilobytes'
    M = 'Megabytes'
    G = 'Gigabytes'
    T = 'Terabytes'
    P = 'Petabytes'
    E = 'Exabytes'


@dataclasses.dataclass(frozen=True)
class BinarySizedValue(ValueObject):
    """
    A sized binary value object
    """
    value: int = dataclasses.field(default=0)
    scale: BinaryScale = dataclasses.field(default=BinaryScale.G)

    def __str__(self):
        return f'{self.value}{self.scale.name}'
