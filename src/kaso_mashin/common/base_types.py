"""
Common Base Types
"""
import abc
import dataclasses
import enum
import typing
import uuid

import pydantic
from pydantic import BaseModel, ConfigDict
from sqlalchemy import UUID, String, select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .. import KasoMashinException


class ValueObject(abc.ABC):
    """
    A domain value object
    """

    pass


class BinaryScale(enum.StrEnum):
    b = "Bytes"
    k = "Kilobytes"
    M = "Megabytes"
    G = "Gigabytes"
    T = "Terabytes"
    P = "Petabytes"
    E = "Exabytes"

    @staticmethod
    def scale_value(scale: "BinaryScale") -> int:
        return {
            BinaryScale.b: 0,
            BinaryScale.k: 1,
            BinaryScale.M: 2,
            BinaryScale.G: 3,
            BinaryScale.T: 4,
            BinaryScale.P: 5,
            BinaryScale.E: 6,
        }[scale]

    def __lt__(self, other) -> bool:
        return BinaryScale.scale_value(self) < BinaryScale.scale_value(other)

    def __gt__(self, other) -> bool:
        return BinaryScale.scale_value(self) > BinaryScale.scale_value(other)


class BinarySizedValue(pydantic.BaseModel):
    """
    A sized binary value object
    """

    value: int = dataclasses.field(default=0)
    scale: BinaryScale = dataclasses.field(default=BinaryScale.G)

    def __init__(self, value: int = 0, scale: BinaryScale = BinaryScale.G):
        super().__init__()
        self.value = value
        self.scale = scale

    def at_scale(self, scale: BinaryScale = BinaryScale.M) -> "BinarySizedValue":
        if self.scale == scale:
            return self
        scale_difference = BinaryScale.scale_value(
            self.scale
        ) - BinaryScale.scale_value(scale)
        if scale_difference == 0:
            return self
        if scale_difference > 0:
            return BinarySizedValue(
                scale=scale, value=int(self.value * (1024**scale_difference))
            )
        return BinarySizedValue(
            scale=scale, value=int(self.value / (1024 ** abs(scale_difference)))
        )

    def __lt__(self, other: "BinarySizedValue") -> bool:
        if any(
            [
                self.scale == other.scale and self.value < other.value,
                self.scale == BinaryScale.E
                and other.scale
                in [
                    BinaryScale.P,
                    BinaryScale.T,
                    BinaryScale.G,
                    BinaryScale.M,
                    BinaryScale.k,
                ],
                self.scale == BinaryScale.P
                and other.scale
                in [BinaryScale.T, BinaryScale.G, BinaryScale.M, BinaryScale.k],
                self.scale == BinaryScale.T
                and other.scale in [BinaryScale.G, BinaryScale.M, BinaryScale.k],
                self.scale == BinaryScale.G
                and other.scale in [BinaryScale.M, BinaryScale.k],
                self.scale == BinaryScale.M and other.scale == BinaryScale.k,
            ]
        ):
            return True
        return False

    def __gt__(self, other: "BinarySizedValue") -> bool:
        return not self.__lt__(other)

    def __str__(self):
        return f"{self.value}{BinaryScale(self.scale).name}"

    def __repr__(self):
        return f"<BinarySizedValue(value={self.value}, scale={self.scale.name})>"


class EntitySchema(BaseModel):
    """
    Schema base class for serialised entities
    """

    model_config = ConfigDict(from_attributes=True)


class ExceptionSchema(pydantic.BaseModel):
    """
    Schema for an exception
    """

    status: int = pydantic.Field(description="The exception status code", default=500)
    msg: str = pydantic.Field(description="A user-readable error description")

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": 400, "msg": "I did not like your input, at all"}]
        }
    }


UniqueIdentifier = uuid.UUID


class EntityNotFoundException(KasoMashinException):
    pass


class EntityInvariantException(KasoMashinException):
    pass


class Service(abc.ABC):
    """
    A domain service
    """

    pass


T_ValueObject = typing.TypeVar("T_ValueObject", bound=ValueObject)
T_EntitySchema = typing.TypeVar("T_EntitySchema", bound=EntitySchema)
T_EntityListSchema = typing.TypeVar("T_EntityListSchema", bound=EntitySchema)
T_EntityListEntrySchema = typing.TypeVar("T_EntityListEntrySchema", bound=EntitySchema)
T_EntityGetSchema = typing.TypeVar("T_EntityGetSchema", bound=EntitySchema)
T_EntityCreateSchema = typing.TypeVar("T_EntityCreateSchema", bound=EntitySchema)
T_EntityModifySchema = typing.TypeVar("T_EntityModifySchema", bound=EntitySchema)


class EntityModel(DeclarativeBase):
    """
    Base class for a persisted entity
    """

    __abstract__ = True
    uid: Mapped[str] = mapped_column(
        UUID(as_uuid=True).with_variant(String(32), "sqlite"), primary_key=True
    )


T_EntityModel = typing.TypeVar("T_EntityModel", bound=EntityModel)


class Entity:
    """
    Base class for a domain entity
    """

    def __init__(self):
        self._uid = uuid.uuid4()

    @property
    def uid(self) -> UniqueIdentifier:
        return self._uid

    def __eq__(self, other: object) -> bool:
        return all(
            [
                isinstance(other, self.__class__),
                self._uid == other.uid,  # type: ignore[attr-defined]
            ]
        )

    def __repr__(self) -> str:
        return f"<Entity(uid={self._uid})>"


T_Entity = typing.TypeVar("T_Entity", bound=Entity)


class AggregateRoot(typing.Generic[T_EntityModel, T_Entity]):
    """
    A marker class for AggregateRoots
    Aggregate roots have two important class attributes that declare their repository and the model class they
    are associated with at runtime. These attributes are set by the repository when it is instantiated.
    """

    runtime: "Runtime" = None
    repository: "AsyncRepository" = None
    model_class: typing.Type[T_EntityModel] = None

    @staticmethod
    @abc.abstractmethod
    async def create(**kwargs) -> "T_AggregateRoot":
        pass

    @staticmethod
    @abc.abstractmethod
    async def from_model(model: T_EntityModel) -> T_Entity:
        pass

    @abc.abstractmethod
    async def to_model(self, model: T_EntityModel | None = None) -> T_EntityModel:
        pass


T_AggregateRoot = typing.TypeVar("T_AggregateRoot", bound=AggregateRoot)


class AsyncRepository(typing.Generic[T_AggregateRoot, T_EntityModel]):

    def __init__(
        self,
        runtime: "Runtime",
        session_maker: async_sessionmaker[AsyncSession],
        aggregate_root_class: typing.Type[T_AggregateRoot],
        model_class: typing.Type[T_EntityModel],
    ):
        self._runtime = runtime
        self._session_maker = session_maker
        self._aggregate_root_class = aggregate_root_class
        self._aggregate_root_class.runtime = runtime
        self._aggregate_root_class.repository = self
        self._aggregate_root_class.model_class = model_class
        self._model_class = model_class

    async def get_by_uid(self, uid: UniqueIdentifier) -> T_Entity:
        async with self._session_maker() as session:
            model = await session.get(self._model_class, str(uid))
            if model is None:
                raise EntityNotFoundException(status=400, msg="No such entity")
            return await self._aggregate_root_class.from_model(model)

    async def list(self) -> typing.List[T_AggregateRoot]:
        async with self._session_maker() as session:
            models = await session.scalars(select(self._model_class))
            return [await self._aggregate_root_class.from_model(m) for m in models]

    async def create(self, entity: T_AggregateRoot) -> T_AggregateRoot:
        async with self._session_maker() as session:
            session.add(await entity.to_model())
            await session.commit()
        return entity

    async def modify(self, entity: T_AggregateRoot) -> T_AggregateRoot:
        async with self._session_maker() as session:
            model = await session.get(self._model_class, str(entity.uid))
            if model is None:
                raise EntityNotFoundException(status=400, msg="No such entity")
            session.add(await entity.to_model(model))
            await session.commit()
        return entity

    async def remove(self, uid: UniqueIdentifier) -> None:
        async with self._session_maker() as session:
            model = await session.get(self._model_class, str(uid))
            if model is not None:
                await session.delete(model)
                await session.commit()
