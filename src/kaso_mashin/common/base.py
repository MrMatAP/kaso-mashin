"""
Common Base Types
"""

import abc
import dataclasses
import enum
import typing
import uuid
import logging

import pydantic
import sqlalchemy
from sqlalchemy import UUID, String, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .exceptions import KasoMashinException, EntityInvariantException, EntityNotFoundException

#
# A consistent type for unique identifiers

UniqueIdentifier = uuid.UUID


@dataclasses.dataclass(frozen=True)
class ValueObject(abc.ABC):
    """
    A domain value object
    """
    pass

T_ValueObject = typing.TypeVar("T_ValueObject", bound=ValueObject)


class Service(abc.ABC):
    """
    A domain service
    """

    def __init__(self):
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

T_Service = typing.TypeVar("T_Service", bound=Service)


class Model(DeclarativeBase):
    """
    Base class for a persisted entity
    """

    __abstract__ = True
    uid: Mapped[str] = mapped_column(
        UUID(as_uuid=True).with_variant(String(32), "sqlite"),
        primary_key=True,
        sort_order=-1
    )
    name: Mapped[str] = mapped_column(String(64))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"


T_Model = typing.TypeVar("T_Model", bound=Model)


class Entity:
    """
    Base class for all domain entities.
    """
    repository: typing.ClassVar['Repository']
    task_service: typing.ClassVar['TaskService']

    def __init__(self, name: str):
        self._uid: UniqueIdentifier = uuid.uuid4()
        self._name = name
        self._dirty = True
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    def uid(self) -> UniqueIdentifier:
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name
        self._dirty = True

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool):
        self._dirty = value

    async def post_create(self) -> None:
        """
        This async hook function is called after the entity is first persisted
        Raises:
            EntityInvariantException
        """
        self._dirty = False

    async def post_modify(self) -> None:
        """
        This async hook function is called after changes to the entity have been persisted
        Raises:
            EntityInvariantException
        """
        self._dirty = False

    async def pre_remove(self) -> None:
        """
        This async hook function is called before the entity is removed from persistence
        Raises:
            EntityInvariantException
        """
        pass

    def __hash__(self) -> int:
        return hash(self._uid)

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            other is not None,
            isinstance(other, self.__class__),
            self._uid == other.uid,
            self._name == other.name
        ])

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(uid={self._uid}, name={self._name})'


T_Entity = typing.TypeVar("T_Entity", bound=Entity)


class AggregateRoot(Entity):
    """
    An aggregate root class.
    Only aggregate roots have save and remove functions.
    """
    async def save(self) -> typing.Self:
        if not self._dirty:
            return self
        await self.repository.create(self)
        return self

    async def remove(self) -> None:
        await self.repository.remove(self)


T_AggregateRoot = typing.TypeVar("T_AggregateRoot", bound=AggregateRoot)


class Repository(typing.Generic[T_Entity, T_Model], abc.ABC):
    """
    Base class for all repositories

    Limitations:
    * typing.ClassVar does not yet support type variables so we might constrain it on the superclass
      but that then further confuses the type checker
    """
    entity_class: typing.Type[T_Entity]
    model_class: typing.Type[T_Model]

    def __init__(self,
                 session_maker: sqlalchemy.ext.asyncio.async_sessionmaker,
                 task_service: 'TaskService') -> None:
        if self.entity_class is None:
            raise KasoMashinException(status=500, msg='Misconfigured DDDRepository without entity')
        if self.model_class is None:
            raise KasoMashinException(status=500, msg='Misconfigured DDDRepository without model')
        self._session_maker = session_maker
        self._identity_map: typing.Dict[UniqueIdentifier, T_Entity] = {}
        self.entity_class.repository = self
        self.entity_class.task_service = task_service

    async def get_by_uid(self, uid: UniqueIdentifier) -> T_Entity:
        try:
            if uid in self._identity_map:
                return self._identity_map[uid]
            async with self._session_maker() as session:
                model = await session.get(self.model_class, str(uid))
                if model is None:
                    raise EntityNotFoundException()
                self._identity_map[uid] = await self.from_model(model)
                return self._identity_map[uid]
        except SQLAlchemyError as sae:
            raise KasoMashinException(status=500, msg='Failure getting an entity by its uid') from sae

    async def get_by_name(self, name: str) -> T_Entity:
        try:
            names = list(filter(lambda e: e.name == name, self._identity_map.values()))
            if len(names) > 0:
                return names[0]
            async with self._session_maker() as session:
                model = (await session.scalars(
                            select(self.model_class)
                            .where(self.model_class.name == name))).one()
                return await self.from_model(model)
        except SQLAlchemyError as sae:
            raise KasoMashinException(status=500, msg='Failure getting an entity by its name') from sae

    async def list(self) -> typing.List[T_Entity]:
        try:
            async with self._session_maker() as session:
                models = (await session.scalars(select(self.model_class))).all()
                return [await self.from_model(m) for m in models]
        except SQLAlchemyError as sae:
            raise KasoMashinException(status=500, msg='Failure listing entities from persistence') from sae

    async def create(self, entity: T_Entity) -> T_Entity:
        try:
            if not issubclass(type(entity), AggregateRoot):
                raise EntityInvariantException(status=400, msg='Only aggregate roots can be created')
            if entity.uid in self._identity_map:
                return await self.modify(entity)
            async with self._session_maker() as session, session.begin():
                model = await self.to_model(entity)
                session.add(model)
                entity._uid = UniqueIdentifier(str(model.uid))
                self._identity_map[entity.uid] = entity
                await entity.post_create()
            return self._identity_map[entity.uid]
        except SQLAlchemyError as sae:
            raise KasoMashinException(status=500, msg='Failure persisting the entities') from sae

    async def modify(self, entity: T_Entity) -> T_Entity:
        try:
            if not entity.uid in self._identity_map:
                raise EntityInvariantException(status=400,
                                               msg='This entity is unknown to the repository')
            async with self._session_maker() as session, session.begin():
                persisted = await session.get(self.model_class, str(entity.uid))
                model = await self.to_model(entity, persisted)
                session.add(model)
                await entity.post_modify()
            return entity
        except SQLAlchemyError as sae:
            raise KasoMashinException(status=500, msg='Failure persisting the entities') from sae

    async def remove(self, entity: T_Entity) -> None:
        try:
            await entity.pre_remove()
            async with self._session_maker() as session, session.begin():
                model = await session.get(self.model_class, str(entity.uid))
                if model is None:
                    raise EntityNotFoundException()
                await session.delete(model)
        except SQLAlchemyError as sae:
            raise KasoMashinException(status=500,
                                      msg='Failure removing the entities in persistent store') from sae

    @classmethod
    @abc.abstractmethod
    async def from_model(cls, model: T_Model, *args, **kwargs) -> T_Entity:
        entity = cls.entity_class(name=model.name, *args, **kwargs)
        entity._uid = UniqueIdentifier(model.uid)
        return entity

    @classmethod
    @abc.abstractmethod
    async def to_model(cls, entity: T_Entity, persisted: T_Model | None = None) -> T_Model:
        if persisted is None:
            model = cls.model_class()
            model.uid = str(entity.uid)
        else:
            model = persisted
        model.name = entity.name
        return model

    def __repr__(self):
        return f'{self.__class__.__name__}({self.entity_class})'


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
        scale_difference = BinaryScale.scale_value(self.scale) - BinaryScale.scale_value(scale)
        if scale_difference == 0:
            return self
        if scale_difference > 0:
            return BinarySizedValue(scale=scale, value=int(self.value * (1024 ** scale_difference)))
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
                    and other.scale in [BinaryScale.T, BinaryScale.G, BinaryScale.M, BinaryScale.k],
                    self.scale == BinaryScale.T
                    and other.scale in [BinaryScale.G, BinaryScale.M, BinaryScale.k],
                    self.scale == BinaryScale.G and other.scale in [BinaryScale.M, BinaryScale.k],
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
