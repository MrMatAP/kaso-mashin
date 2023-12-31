import abc
import typing

import sqlalchemy.orm


class Base(sqlalchemy.orm.DeclarativeBase):  # pylint: disable=too-few-public-methods
    """
    Base class for database persistence
    """
    pass


class EntityModel:
    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(32),
                                                                  primary_key=True)

    def merge(self, other: 'EntityModel'):
        for key, value in self.__dict__.items():
            if key == id:
                continue
            setattr(self, key, getattr(other, key))


T = typing.TypeVar('T', bound=EntityModel, covariant=True)
UniqueIdentifier = typing.TypeVar('UniqueIdentifier', str, sqlalchemy.UUID(as_uuid=True))


class Entity(abc.ABC):
    pass


class ValueObject(abc.ABC):
    pass


class AggregateRoot(Entity):
    pass


class Repository(typing.Generic[T]):

    def __init__(self, model: typing.Type[T], session: sqlalchemy.orm.Session) -> None:
        self._model = model
        self._session = session

    def get_by_id(self, uid: UniqueIdentifier) -> T:
        return self._session.get(self._model, str(uid))

    def list(self) -> typing.Iterable[T]:
        return self._session.query(self._model).all()

    def create(self, entity: T) -> T:
        self._session.add(entity)
        self._session.commit()
        return entity

    def modify(self, update: T) -> T:
        current: T = self._session.get(self._model, update.id)
        current.merge(update)
        self._session.add(current)
        self._session.commit()
        return current

    def remove(self, uid: UniqueIdentifier) -> None:
        current = self._session.get(self._model, str(uid))
        self._session.delete(current)
        self._session.commit()



