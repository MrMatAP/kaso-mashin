import typing

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from .base_types import (
    UniqueIdentifier,
    T_AggregateRoot, T_AggregateRootModel,
    EntityNotFoundException)


class Repository(typing.Generic[T_AggregateRoot]):

    def __init__(self,
                 aggregate_root_clazz: typing.Type[T_AggregateRoot],
                 model_clazz: typing.Type[T_AggregateRootModel],
                 session_maker: sessionmaker):
        self._aggregate_root_clazz = aggregate_root_clazz
        self._model_clazz = model_clazz
        self._session_maker = session_maker
        self._identity_map: typing.Dict[UniqueIdentifier, T_AggregateRoot] = {}

    def get_by_id(self, uid: UniqueIdentifier) -> T_AggregateRoot:
        if uid in self._identity_map:
            return self._identity_map[uid]
        with self._session_maker() as session:
            model = session.get(self._model_clazz, str(uid))
            if model is None:
                raise EntityNotFoundException(code=400, msg='No such entity')
            self._identity_map[uid] = self._aggregate_root_clazz.deserialise(model)
        return self._identity_map[uid]

    def list(self) -> typing.List[T_AggregateRoot]:
        with self._session_maker() as session:
            for model in session.scalars(select(self._model_clazz)).all():
                self._identity_map[UniqueIdentifier(model.id)] = self._aggregate_root_clazz.deserialise(model)
        # Note: list() is semantically better but mypy complains about an incompatible arg
        return [i for i in self._identity_map.values()]

    def create(self, aggregate_root: T_AggregateRoot) -> T_AggregateRoot:
        with self._session_maker() as session:
            with session.begin():
                session.add(aggregate_root.serialise())
            self._identity_map[aggregate_root.id] = aggregate_root
        return aggregate_root

    def modify(self, update: T_AggregateRoot) -> T_AggregateRoot:
        with self._session_maker() as session:
            current = session.get(self._model_clazz, str(update.id))
            if current is None:
                raise EntityNotFoundException(code=400, msg='No such entity')
            current.update(update.serialise())
            session.add(current)
            session.commit()
            self._identity_map[update.id] = update
        return update

    def remove(self, uid: UniqueIdentifier) -> None:
        with self._session_maker() as session:
            model = session.get(self._model_clazz, str(uid))
            if model is not None:
                session.delete(model)
                session.commit()
            del self._identity_map[uid]
