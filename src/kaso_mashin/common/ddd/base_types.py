import abc
import typing
import enum

import sqlalchemy.orm


class Base(sqlalchemy.orm.DeclarativeBase):  # pylint: disable=too-few-public-methods
    """
    Base class for database persistence
    """
    pass


class EntityModel:
    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(32), primary_key=True)

    @staticmethod
    @abc.abstractmethod
    def from_aggregateroot(entity):
        raise NotImplementedError()

    @abc.abstractmethod
    def as_entity(self):
        raise NotImplementedError()

    def merge(self, other: 'EntityModel'):
        for key, value in self.__dict__.items():
            if key == id:
                continue
            setattr(self, key, getattr(other, key))


T = typing.TypeVar('T', bound=EntityModel)
UniqueIdentifier = typing.TypeVar('UniqueIdentifier', str, sqlalchemy.UUID(as_uuid=True))


class BinaryScale(enum.StrEnum):
    KB = 'Kilobytes'
    MB = 'Megabytes'
    GB = 'Gigabytes'
    TB = 'Terabytes'


class Entity(abc.ABC):
    pass


class ValueObject(abc.ABC):
    pass


class Aggregate(Entity):
    pass


class AggregateRoot(Aggregate):
    pass


class Repository(typing.Generic[T]):
    """
    A generic repository operating on type T and instantiated as Repository[DiskModel](DiskModel, session). It is
    unfortunate that we have to specify the model twice in the constructor but due to type erasure, the type of
    T is no longer known at runtime. This is easily solved for those methods that accept a typed parameter (e.g.
    a DiskModel instance) but not for those cases where we simply accept a unique identifier.
    """

    def __init__(self, model: typing.Type[T], session: sqlalchemy.orm.Session) -> None:
        self._model = model
        self._session = session
        self._identity_map: typing.Dict[UniqueIdentifier, T] = {}

    def get_by_id(self, uid: UniqueIdentifier) -> T | None:
        """
        Return a model instance by its unique identifier. Models are cached in an identity map to minimise (potentially costly)
        lookups into the datastore.
        Args:
            uid: The unique identifier of the model instance.

        Returns:

        """
        if uid in self._identity_map:
            return self._identity_map[uid]
        self._identity_map[uid] = self._session.get(self._model, str(uid))
        return self._identity_map[uid]

    def list(self) -> typing.Iterable[T]:
        """
        List all currently known model instances
        Returns:
            An iterable containing all known model instances.
        """
        self._identity_map.update({e.id: e for e in self._session.query(self._model).all()})
        return self._identity_map.values()

    def create(self, instance: T) -> T:
        """
        Create a new model instance
        Args:
            instance: The model instance to create

        Returns:
            The persisted model instance
        """
        self._session.add(instance)
        self._session.commit()
        self._identity_map[instance.id] = instance
        return instance

    def modify(self, update: T) -> T:
        """
        Update an existing model instance
        Args:
            update: The updated model instance

        Returns:
            The updated model instance
        """
        current: T = self._session.get(type(update), update.id)
        current.merge(update)
        self._session.add(current)
        self._session.commit()
        self._identity_map[current.id] = current
        return current

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
