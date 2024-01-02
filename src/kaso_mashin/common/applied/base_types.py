import abc
import typing
import enum
import dataclasses
import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column


class BinaryScale(enum.StrEnum):
    k = 'Kilobytes'
    M = 'Megabytes'
    G = 'Gigabytes'
    T = 'Terabytes'
    P = 'Petabytes'
    E = 'Exabytes'


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """
    Base class for database persistence
    """
    pass


class Entity(abc.ABC):
    """
    A domain entity
    """


class ValueObject(abc.ABC):
    """
    A domain value object
    """
    pass


@dataclasses.dataclass
class AggregateRoot(Entity):
    """
    An aggregate root mixin for entities
    """
    pass


class AggregateRootModel:
    """
    Representation of an entity in the database
    """
    id: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'), primary_key=True)

    def merge(self, other: 'AggregateRootModel'):
        for key, value in self.__dict__.items():
            if key == id:
                continue
            setattr(self, key, getattr(other, key))


T_Entity = typing.TypeVar('T_Entity', bound=Entity)
T_AggregateRoot = typing.TypeVar('T_AggregateRoot', bound=AggregateRoot)
T_AggregateRootModel = typing.TypeVar('T_AggregateRootModel', bound=AggregateRootModel)
UniqueIdentifier = typing.TypeVar('UniqueIdentifier', bound=uuid.UUID)


class Repository(typing.Generic[T_AggregateRoot, T_AggregateRootModel]):
    """
    A generic repository operating on type T and instantiated as Repository[DiskModel](DiskModel, session). It is
    unfortunate that we have to specify the model twice in the constructor but due to type erasure, the type of
    T is no longer known at runtime. This is easily solved for those methods that accept a typed parameter (e.g.
    a DiskModel instance) but not for those cases where we simply accept a unique identifier.

    It is recommended to create a typedef EntityRepository = Repository[Entity] to avoid a runtime performance hit
    """

    def __init__(self, model: typing.Type[T_AggregateRootModel], session: Session) -> None:
        self._model = model
        self._session = session
        self._identity_map: typing.Dict[UniqueIdentifier, T_AggregateRoot] = {}

    @abc.abstractmethod
    def marshal(self, entity: T_AggregateRoot) -> T_AggregateRootModel:
        """
        Marshal a domain object into a model suitable for persisting it
        Returns:
            An instance of T_AggregateRootModel, suitable for persistence
        """
        pass

    def merge(self, update: T_AggregateRoot, model: T_AggregateRootModel) -> T_AggregateRootModel:
        """
        Merge an update from a existing aggregate root into an existing model suitable for persistence
        Args:
            update: The domain object containing the update
            model: The model to merge with

        Returns:
            The updated model
        """
        for attr in dataclasses.fields(update):
            if attr.name == 'id':
                continue
            setattr(model, attr.name, getattr(update, attr.name))
        return model

    @abc.abstractmethod
    def unmarshal(self, model: T_AggregateRootModel) -> T_AggregateRoot:
        """
        Unmarshal an aggregate root model from its persisted representation into its corresponding domain
        aggregate root
        Returns:
            An instance of the domain aggregate root T_AggregateRoot
        """
        pass

    def get_by_id(self, uid: UniqueIdentifier) -> T_AggregateRoot | None:
        """
        Return a model instance by its unique identifier. Models are cached in an identity map to minimise (potentially costly)
        lookups into the datastore.
        Args:
            uid: The unique identifier of the model instance.

        Returns:

        """
        if uid in self._identity_map:
            return self._identity_map[uid]
        model = self._session.get(self._model, str(uid))
        self._identity_map[uid] = self.unmarshal(model) if model is not None else None
        return self._identity_map[uid]

    def list(self) -> typing.List[T_AggregateRoot]:
        """
        List all currently known model instances
        Returns:
            An iterable containing all known model instances.
        """
        self._identity_map.update({e.id: self.unmarshal(e) for e in self._session.query(self._model).all()})
        return list(self._identity_map.values())

    def create(self, entity: T_AggregateRoot) -> T_AggregateRoot:
        """
        Create a new entity
        Args:
            entity: The model instance to create

        Returns:
            The persisted model instance
        """
        self._session.add(self.marshal(entity))
        self._session.commit()
        self._identity_map[entity.id] = entity
        return entity

    def modify(self, update: T_AggregateRoot) -> T_AggregateRoot:
        """
        Update an existing model instance
        Args:
            update: The updated model instance

        Returns:
            The updated model instance
        """
        model = self._session.get(self._model, update.id)
        self._session.add(self.merge(update, model))
        self._session.commit()
        self._identity_map[update.id] = update
        return update

    def remove(self, uid: UniqueIdentifier) -> None:
        """
        Remove an existing model instance
        Args:
            uid: The unique identifier of the model instance to be removed
        """
        current = self._session.get(self._model, str(uid))
        self._session.delete(current)
        self._session.commit()
        del self._identity_map[uid]


@dataclasses.dataclass(frozen=True)
class BinarySizedValue(ValueObject):
    """
    A sized binary value object
    """
    value: int = dataclasses.field(default=0)
    scale: BinaryScale = dataclasses.field(default=BinaryScale.G)

    def __str__(self):
        return f'{self.value}{self.scale.name}'


class KMException(Exception):

    def __init__(self, code: int, msg: str) -> None:
        super().__init__()
        self._code = code
        self._msg = msg

    def __str__(self) -> str:
        return f'[{self._code}] {self._msg}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(code={self._code}, msg={self._msg})'
