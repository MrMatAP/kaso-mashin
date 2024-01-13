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


class EntityInvariantException(KasoMashinException):
    pass


class ORMBase(DeclarativeBase):
    """
    ORM base class for persisted entities
    """
    id: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'), primary_key=True)

    @abc.abstractmethod
    def merge(self, other: typing.Self):
        pass


UniqueIdentifier = uuid.UUID
T_Model = typing.TypeVar('T_Model', bound=ORMBase)


@dataclasses.dataclass
class Entity(typing.Generic[T_Model]):
    """
    A domain entity
    """
    # TODO: Owner should be either T_AggregateRoot or T_AsyncAggregateRoot
    id: UniqueIdentifier = dataclasses.field(default_factory=lambda: uuid.uuid4())
    owner: typing.Optional[typing.Any] = dataclasses.field(default=None)


T_Entity = typing.TypeVar("T_Entity", bound=Entity)


class ValueObject(abc.ABC):
    """
    A domain value object
    """
    pass


T_ValueObject = typing.TypeVar('T_ValueObject', bound=ValueObject)


class AsyncAggregateRoot(typing.Generic[T_Entity, T_Model]):

    def __init__(self, model: typing.Type[T_Model], session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._repository = AsyncRepository[T_Model](model=model, session_maker=session_maker)
        self._identity_map: typing.Dict[UniqueIdentifier, T_Entity] = {}

    async def get(self, uid: UniqueIdentifier) -> T_Entity:
        model = await self._repository.get_by_id(str(uid))
        entity = await self.from_model(model)
        if not await self.validate(entity):
            raise EntityInvariantException(code=500, msg='Restored entity fails validation')
        entity.owner = self
        self._identity_map[entity.id] = entity
        return self._identity_map[entity.id]

    async def list(self) -> typing.List[T_Entity]:
        models = await self._repository.list()
        entities = [await self.from_model(model) for model in models]
        for entity in entities:
            if not await self.validate(entity):
                raise EntityInvariantException(code=500, msg='Entity fails validation')
            entity.owner = self
        self._identity_map.update({e.id: e for e in entities})
        return list(self._identity_map.values())

    async def create(self, entity: T_Entity) -> T_Entity:
        if not self.validate(entity):
            raise EntityInvariantException(code=500, msg='Entity fails validation')
        model = await self._repository.create(await self.to_model(entity))
        self._identity_map[entity.id] = await self.from_model(model)
        self._identity_map[entity.id].owner = self
        return self._identity_map[entity.id]

    # TODO: Modify may make sense to be moved into the entity
    async def modify(self, entity: T_Entity) -> T_Entity:
        if entity.id not in self._identity_map:
            raise EntityInvariantException(code=400, msg='Entity was not created by its aggregate root')
        if not self.validate(entity):
            raise EntityInvariantException(code=400, msg='Entity fails validation')
        model = await self._repository.modify(await self.to_model(entity))
        self._identity_map[entity.id] = await self.from_model(model)
        self._identity_map[entity.id].owner = self
        return self._identity_map[entity.id]

    # TODO: Modify may make sense to be moved into the entity
    async def remove(self, uid: UniqueIdentifier):
        if uid not in self._identity_map:
            raise EntityInvariantException(code=400, msg='Entity was not created by its aggregate root')
        await self._repository.remove(str(uid))
        del self._identity_map[uid]

    async def validate(self, entity: T_Entity) -> bool:
        return True

    @abc.abstractmethod
    async def to_model(self, entity: T_Entity) -> T_Model:
        pass

    @abc.abstractmethod
    async def from_model(self, model: T_Model) -> T_Entity:
        pass


T_AsyncAggregateRoot = typing.TypeVar('T_AsyncAggregateRoot', bound=AsyncAggregateRoot)


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


class AsyncRepository(typing.Generic[T_Model]):

    def __init__(self,
                 model: typing.Type[T_Model],
                 session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._model_clazz = model
        self._session_maker = session_maker
        self._identity_map: typing.Dict[str, T_Model] = {}

    async def get_by_id(self, uid: str) -> T_Model:
        if uid in self._identity_map:
            return self._identity_map[uid]
        async with self._session_maker() as session:
            model = await session.get(self._model_clazz, str(uid))
            if model is None:
                raise EntityNotFoundException(code=400, msg='No such entity')
            self._identity_map[uid] = model
            return self._identity_map[uid]

    async def list(self) -> typing.List[T_Model]:
        async with self._session_maker() as session:
            # Alternative implementation
            # with await session.stream_scalars(select(self._model_clazz)) as result:
            #     models = await result.all()
            #     for model in models:
            #         self._identity_map[UniqueIdentifier(model.id)] = self._aggregate_root_clazz.deserialise(model)
            models = await session.scalars(select(self._model_clazz))
            for model in models:
                self._identity_map[model.id] = model
        # Note: list() is semantically better but mypy complains about an incompatible arg
        return [i for i in self._identity_map.values()]

    async def create(self, model: T_Model) -> T_Model:
        async with self._session_maker() as session:
            async with session.begin():
                session.add(model)
            self._identity_map[model.id] = model
        return model

    async def modify(self, update: T_Model) -> T_Model:
        async with self._session_maker() as session:
            current = await session.get(self._model_clazz, str(update.id))
            if current is None:
                raise EntityNotFoundException(code=400, msg='No such entity')
            current.merge(update)
            session.add(current)
            await session.commit()
            self._identity_map[update.id] = update
        return update

    async def remove(self, uid: str) -> None:
        async with self._session_maker() as session:
            model = await session.get(self._model_clazz, str(uid))
            if model is not None:
                await session.delete(model)
                await session.commit()
            del self._identity_map[uid]
