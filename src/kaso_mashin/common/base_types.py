"""
Common Base Types
"""
import abc
import dataclasses
import enum
import typing
import uuid

from sqlalchemy import UUID, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from pydantic import BaseModel, ConfigDict, Field

from kaso_mashin import KasoMashinException


class EntityNotFoundException(KasoMashinException):
    pass


class EntityInvariantException(KasoMashinException):
    pass


class EntityMaterialisationException(KasoMashinException):
    pass


class ORMBase(DeclarativeBase):
    """
    ORM base class for persisted entities
    """
    uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'), primary_key=True)

    @abc.abstractmethod
    def merge(self, other: typing.Self):
        pass


UniqueIdentifier = uuid.UUID
T_Model = typing.TypeVar('T_Model', bound=ORMBase)


class SchemaBase(BaseModel):
    """
    Schema base class for serialised entities
    """
    model_config = ConfigDict(from_attributes=True)


T_Schema = typing.TypeVar('T_Schema', bound=SchemaBase)


class ValueObject(abc.ABC):
    """
    A domain value object
    """
    pass


T_ValueObject = typing.TypeVar('T_ValueObject', bound=ValueObject)


class Entity:
    """
    A domain base entity

    All domain entities have a unique identity and a corresponding aggregate root as their owner
    """

    def __init__(self, owner: 'AggregateRoot') -> None:
        self._uid = uuid.uuid4()
        self._owner = owner

    @property
    def uid(self) -> UniqueIdentifier:
        return self._uid

    @property
    def owner(self) -> 'AggregateRoot':
        return self._owner

    def __eq__(self, other: object) -> bool:
        return all([
            isinstance(other, self.__class__),
            self._uid == other.uid,            # type: ignore[attr-defined]
            self._owner == other.owner         # type: ignore[attr-defined]
        ])

    def __repr__(self) -> str:
        return f'<Entity(uid={self._uid})'


T_Entity = typing.TypeVar("T_Entity", bound=Entity)


class AggregateRoot(typing.Generic[T_Entity, T_Model]):

    def __init__(self,
                 model: typing.Type[T_Model],
                 session_maker: async_sessionmaker[AsyncSession],
                 runtime: 'Runtime'):
        self._runtime = runtime
        self._repository = AsyncRepository[T_Model](model=model, session_maker=session_maker)
        self._identity_map: typing.Dict[UniqueIdentifier, T_Entity] = {}

    async def get(self, uid: UniqueIdentifier, force_reload: bool = False) -> T_Entity:
        if not force_reload and uid in self._identity_map:
            return self._identity_map[uid]
        model = await self._repository.get_by_uid(str(uid))
        entity = await self._from_model(model)
        if not self.validate(entity):
            raise EntityInvariantException(status=500, msg='Restored entity fails validation')
        self._identity_map[entity.uid] = entity
        return self._identity_map[entity.uid]

    async def list(self, force_reload: bool = False) -> typing.List[T_Entity]:
        if not force_reload:
            return list(self._identity_map.values())
        models = await self._repository.list()
        entities = [await self._from_model(model) for model in models]
        for entity in entities:
            if not self.validate(entity):
                raise EntityInvariantException(status=400, msg='Entity fails validation')
        self._identity_map.update({e.uid: e for e in entities})
        return list(self._identity_map.values())

    async def create(self, entity: T_Entity) -> T_Entity:
        if entity.uid in self._identity_map:
            raise EntityInvariantException(status=400, msg='Entity already exists')
        if not self.validate(entity):
            raise EntityInvariantException(status=400, msg='Entity fails validation')
        model = await self._repository.create(await self._to_model(entity))
        self._identity_map[entity.uid] = await self._from_model(model)
        return self._identity_map[entity.uid]

    # Only methods in the entity should call this
    async def modify(self, entity: T_Entity):
        if entity.uid not in self._identity_map:
            raise EntityNotFoundException(status=400, msg='Entity was not created by this aggregate root')
        if not self.validate(entity):
            raise EntityInvariantException(status=400, msg='Entity fails validation')
        await self._repository.modify(await self._to_model(entity))

    # An entity should only be removed using this method
    async def remove(self, uid: UniqueIdentifier):
        if uid not in self._identity_map:
            raise EntityNotFoundException(status=400, msg='Entity was not created by this aggregate root')
        await self._repository.remove(str(uid))
        del self._identity_map[uid]

    def validate(self, entity: T_Entity) -> bool:
        return all([
            entity is not None,
            isinstance(entity.uid, UniqueIdentifier)
        ])

    @abc.abstractmethod
    async def _to_model(self, entity: T_Entity) -> T_Model:
        pass

    @abc.abstractmethod
    async def _from_model(self, model: T_Model) -> T_Entity:
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


class BinarySizedValueSchema(SchemaBase):
    value: int = Field(description="The value", examples=[2, 4, 8])
    scale: BinaryScale = Field(description="The binary scale", examples=[BinaryScale.M, BinaryScale.G, BinaryScale.T])


class AsyncRepository(typing.Generic[T_Model]):

    def __init__(self,
                 model: typing.Type[T_Model],
                 session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._model_clazz = model
        self._session_maker = session_maker
        self._identity_map: typing.Dict[str, T_Model] = {}

    async def get_by_uid(self, uid: str) -> T_Model:
        if uid in self._identity_map:
            return self._identity_map[uid]
        async with self._session_maker() as session:
            model = await session.get(self._model_clazz, str(uid))
            if model is None:
                raise EntityNotFoundException(status=400, msg='No such entity')
            self._identity_map[uid] = model
            return self._identity_map[uid]

    async def list(self) -> typing.List[T_Model]:
        async with self._session_maker() as session:
            models = await session.scalars(select(self._model_clazz))
            for model in models:
                self._identity_map[model.uid] = model
        # Note: list() is semantically better but mypy complains about an incompatible arg
        return [i for i in self._identity_map.values()]

    async def create(self, model: T_Model) -> T_Model:
        async with self._session_maker() as session:
            session.add(model)
            await session.commit()
            self._identity_map[model.uid] = model
        return model

    async def modify(self, update: T_Model) -> T_Model:
        async with self._session_maker() as session:
            current = await session.get(self._model_clazz, str(update.uid))
            if current is None:
                raise EntityNotFoundException(status=400, msg='No such entity')
            current.merge(update)
            session.add(current)
            await session.commit()
            self._identity_map[update.uid] = update
        return update

    async def remove(self, uid: str) -> None:
        async with self._session_maker() as session:
            model = await session.get(self._model_clazz, str(uid))
            if model is not None:
                await session.delete(model)
                await session.commit()
            del self._identity_map[uid]


