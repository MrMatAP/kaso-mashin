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


class ValueObject(abc.ABC):
    """
    A domain value object
    """
    pass


T_ValueObject = typing.TypeVar('T_ValueObject', bound=ValueObject)


class Entity(object):
    """
    A domain entity
    """

    def __init__(self, owner: 'AggregateRoot', uid: UniqueIdentifier = uuid.uuid4()) -> None:
        self._uid = uid
        self._owner = owner

    @property
    def uid(self) -> UniqueIdentifier:
        return self._uid

    def __eq__(self, other: object) -> bool:
        return all([
            isinstance(other, self.__class__),
            self._uid == other._uid,            # type: ignore[attr-defined]
            self._owner == other._owner         # type: ignore[attr-defined]
        ])


T_Entity = typing.TypeVar("T_Entity", bound=Entity)


class AggregateRoot(typing.Generic[T_Entity, T_Model]):

    def __init__(self, model: typing.Type[T_Model], session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._repository = AsyncRepository[T_Model](model=model, session_maker=session_maker)
        self._identity_map: typing.Dict[UniqueIdentifier, T_Entity] = {}

    async def get(self, uid: UniqueIdentifier, force_reload: bool = False) -> T_Entity:
        if not force_reload and uid in self._identity_map:
            return self._identity_map[uid]
        model = await self._repository.get_by_uid(str(uid))
        entity = await self._from_model(model)
        if not await self._validate(entity):
            raise EntityInvariantException(code=500, msg='Restored entity fails validation')
        self._identity_map[entity.uid] = entity
        return self._identity_map[entity.uid]

    async def list(self, force_reload: bool = False) -> typing.List[T_Entity]:
        if not force_reload:
            return list(self._identity_map.values())
        models = await self._repository.list()
        entities = [await self._from_model(model) for model in models]
        for entity in entities:
            if not await self._validate(entity):
                raise EntityInvariantException(code=400, msg='Entity fails validation')
        self._identity_map.update({e.uid: e for e in entities})
        return list(self._identity_map.values())

    async def create(self, entity: T_Entity) -> T_Entity:
        if entity.uid in self._identity_map:
            raise EntityInvariantException(code=400, msg='Entity already exists')
        if not self._validate(entity):
            raise EntityInvariantException(code=400, msg='Entity fails validation')
        model = await self._repository.create(await self._to_model(entity))
        self._identity_map[entity.uid] = await self._from_model(model)
        return self._identity_map[entity.uid]

    # Only methods in the entity should call this
    async def modify(self, entity: T_Entity):
        if entity.uid not in self._identity_map:
            raise EntityInvariantException(code=400, msg='Entity was not created by its aggregate root')
        if not self._validate(entity):
            raise EntityInvariantException(code=400, msg='Entity fails validation')
        await self._repository.modify(await self._to_model(entity))

    # An entity should only be removed using this method
    async def remove(self, uid: UniqueIdentifier):
        if uid not in self._identity_map:
            raise EntityInvariantException(code=400, msg='Entity was not created by its aggregate root')
        await self._repository.remove(str(uid))
        del self._identity_map[uid]

    async def _validate(self, entity: T_Entity) -> bool:
        return True

    @abc.abstractmethod
    async def _to_model(self, entity: T_Entity) -> T_Model:
        pass

    @abc.abstractmethod
    async def _from_model(self, model: T_Model) -> T_Entity:
        pass


T_AggregateRoot = typing.TypeVar('T_AggregateRoot', bound=AggregateRoot)


class DiskFormat(enum.StrEnum):
    Raw = 'raw'
    QCoW2 = 'qcow2'
    VDI = 'vdi'


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

    async def get_by_uid(self, uid: str) -> T_Model:
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
                raise EntityNotFoundException(code=400, msg='No such entity')
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


