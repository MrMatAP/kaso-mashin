import typing

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from .base_types import (
    UniqueIdentifier,
    T_AggregateRoot, T_AggregateRootModel,
    EntityNotFoundException)


class AsyncRepository(typing.Generic[T_AggregateRoot]):

    def __init__(self,
                 aggregate_root_clazz: typing.Type[T_AggregateRoot],
                 model_clazz: typing.Type[T_AggregateRootModel],
                 session_maker: async_sessionmaker[AsyncSession]):
        self._aggregate_root_clazz = aggregate_root_clazz
        self._model_clazz = model_clazz
        self._session_maker = session_maker
        self._identity_map: typing.Dict[UniqueIdentifier, T_AggregateRoot] = {}

    async def get_by_id(self, uid: UniqueIdentifier) -> T_AggregateRoot:
        if uid in self._identity_map:
            return self._identity_map[uid]
        async with self._session_maker() as session:
            model = await session.get(self._model_clazz, str(uid))
            if model is None:
                raise EntityNotFoundException(code=400, msg='No such entity')
            self._identity_map[uid] = self._aggregate_root_clazz.deserialise(model)
            return self._identity_map[uid]

    async def list(self) -> typing.List[T_AggregateRoot]:
        async with self._session_maker() as session:
            # Alternative implementation
            # with await session.stream_scalars(select(self._model_clazz)) as result:
            #     models = await result.all()
            #     for model in models:
            #         self._identity_map[UniqueIdentifier(model.id)] = self._aggregate_root_clazz.deserialise(model)
            models = await session.scalars(select(self._model_clazz))
            for model in models:
                self._identity_map[UniqueIdentifier(model.id)] = self._aggregate_root_clazz.deserialise(model)
        # Note: list() is semantically better but mypy complains about an incompatible arg
        return [i for i in self._identity_map.values()]

    async def create(self, aggregate_root: T_AggregateRoot) -> T_AggregateRoot:
        async with self._session_maker() as session:
            async with session.begin():
                session.add(aggregate_root.serialise())
            self._identity_map[aggregate_root.id] = aggregate_root
        return aggregate_root

    async def modify(self, update: T_AggregateRoot) -> T_AggregateRoot:
        async with self._session_maker() as session:
            current = await session.get(self._model_clazz, str(update.id))
            if current is None:
                raise EntityNotFoundException(code=400, msg='No such entity')
            current.update(update.serialise())
            session.add(current)
            await session.commit()
            self._identity_map[update.id] = update
        return update

    async def remove(self, uid: UniqueIdentifier) -> None:
        async with self._session_maker() as session:
            model = await session.get(self._model_clazz, str(uid))
            if model is not None:
                await session.delete(model)
                await session.commit()
            del self._identity_map[uid]
