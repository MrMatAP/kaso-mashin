import abc
import typing
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import UUID, String, select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from kaso_mashin import KasoMashinException


UniqueIdentifier = uuid.UUID


class EntityNotFoundException(KasoMashinException):
    pass


class EntityInvariantException(KasoMashinException):
    pass


class ValueObject(abc.ABC):
    """
    A domain value object
    """
    pass


T_ValueObject = typing.TypeVar('T_ValueObject', bound=ValueObject)


class EntitySchema(BaseModel):
    """
    Schema base class for serialised entities
    """
    model_config = ConfigDict(from_attributes=True)


T_EntitySchema = typing.TypeVar('T_EntitySchema', bound=EntitySchema)


class EntityModel(DeclarativeBase):
    """
    Base class for a persisted entity
    """
    __abstract__ = True
    uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'),
                                     primary_key=True)


T_EntityModel = typing.TypeVar('T_EntityModel', bound=EntityModel)


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
        return all([
            isinstance(other, self.__class__),
            self._uid == other.uid            # type: ignore[attr-defined]
        ])

    def __repr__(self) -> str:
        return f'<Entity(uid={self._uid})>'


T_Entity = typing.TypeVar("T_Entity", bound=Entity)


class AggregateRoot(typing.Generic[T_EntityModel, T_Entity]):
    """
    A marker class for AggregateRoots
    Aggregate roots have two important class attributes that declare their repository and the model class they
    are associated with at runtime. These attributes are set by the repository when it is instantiated.
    """
    repository: 'AsyncRepository' = None
    model_class: typing.Type[T_EntityModel] = None

    @staticmethod
    @abc.abstractmethod
    async def create(**kwargs) -> 'T_AggregateRoot':
        pass

    @staticmethod
    @abc.abstractmethod
    def from_model(model: T_EntityModel) -> T_Entity:
        pass

    @abc.abstractmethod
    def to_model(self, model: T_EntityModel | None = None) -> T_EntityModel:
        pass


T_AggregateRoot = typing.TypeVar('T_AggregateRoot', bound=AggregateRoot)


class AsyncRepository(typing.Generic[T_AggregateRoot, T_EntityModel]):

    def __init__(self,
                 session_maker: async_sessionmaker[AsyncSession],
                 aggregate_root_class: typing.Type[T_AggregateRoot],
                 model_class: typing.Type[T_EntityModel]):
        self._session_maker = session_maker
        self._aggregate_root_class = aggregate_root_class
        self._aggregate_root_class.repository = self
        self._aggregate_root_class.model_class = model_class
        self._model_class = model_class

    async def get_by_uid(self, uid: UniqueIdentifier) -> T_Entity:
        async with self._session_maker() as session:
            model = await session.get(self._model_class, str(uid))
            if model is None:
                raise EntityNotFoundException(status=400, msg='No such entity')
            return self._aggregate_root_class.from_model(model)

    async def list(self) -> typing.List[T_AggregateRoot]:
        async with self._session_maker() as session:
            models = await session.scalars(select(self._model_class))
            return [self._aggregate_root_class.from_model(m) for m in models]

    async def create(self, entity: T_AggregateRoot) -> T_AggregateRoot:
        async with self._session_maker() as session:
            session.add(entity.to_model())
            await session.commit()
        return entity

    async def modify(self, entity: T_AggregateRoot) -> T_AggregateRoot:
        async with self._session_maker() as session:
            model = await session.get(self._model_class, str(entity.uid))
            if model is None:
                raise EntityNotFoundException(status=400, msg='No such entity')
            session.add(entity.to_model(model))
            await session.commit()
        return entity

    async def remove(self, uid: UniqueIdentifier) -> None:
        async with self._session_maker() as session:
            model = await session.get(self._model_class, str(uid))
            if model is not None:
                await session.delete(model)
                await session.commit()
