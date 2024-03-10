"""
Common Base Types
"""
import dataclasses
import enum

from pydantic import Field

from .ddd_scaffold import (
    ValueObject,
    EntitySchema
)


class BinaryScale(enum.StrEnum):
    k = 'Kilobytes'
    M = 'Megabytes'
    G = 'Gigabytes'
    T = 'Terabytes'
    P = 'Petabytes'
    E = 'Exabytes'


class BinarySizedValueSchema(EntitySchema):
    value: int = Field(description="The value", examples=[2, 4, 8])
    scale: BinaryScale = Field(description="The binary scale", examples=[BinaryScale.M, BinaryScale.G, BinaryScale.T])


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


# class AggregateRootOld(typing.Generic[T_Entity, T_EntityModel]):
#
#     def __init__(self,
#                  model: typing.Type[T_EntityModel],
#                  session_maker: async_sessionmaker[AsyncSession],
#                  runtime: 'Runtime'):
#         self._runtime = runtime
#         self._repository = AsyncRepository[T_EntityModel](model=model, session_maker=session_maker)
#         self._identity_map: typing.Dict[UniqueIdentifier, T_Entity] = {}
#
#     async def get(self, uid: UniqueIdentifier, force_reload: bool = False) -> T_Entity:
#         if not force_reload and uid in self._identity_map:
#             return self._identity_map[uid]
#         model = await self._repository.get_by_uid(str(uid))
#         entity = await self._from_model(model)
#         if not self.validate(entity):
#             raise EntityInvariantException(status=500, msg='Restored entity fails validation')
#         self._identity_map[entity.uid] = entity
#         return self._identity_map[entity.uid]
#
#     async def list(self, force_reload: bool = False) -> typing.List[T_Entity]:
#         if not force_reload:
#             return list(self._identity_map.values())
#         models = await self._repository.list()
#         entities = [await self._from_model(model) for model in models]
#         for entity in entities:
#             if not self.validate(entity):
#                 raise EntityInvariantException(status=400, msg='Entity fails validation')
#         self._identity_map.update({e.uid: e for e in entities})
#         return list(self._identity_map.values())
#
#     async def create(self, entity: T_Entity) -> T_Entity:
#         if entity.uid in self._identity_map:
#             raise EntityInvariantException(status=400, msg='Entity already exists')
#         if not self.validate(entity):
#             raise EntityInvariantException(status=400, msg='Entity fails validation')
#         model = await self._repository.create(await self._to_model(entity))
#         self._identity_map[entity.uid] = await self._from_model(model)
#         return self._identity_map[entity.uid]
#
#     # Only methods in the entity should call this
#     async def modify(self, entity: T_Entity):
#         if entity.uid not in self._identity_map:
#             raise EntityNotFoundException(status=400, msg='Entity was not created by this aggregate root')
#         if not self.validate(entity):
#             raise EntityInvariantException(status=400, msg='Entity fails validation')
#         await self._repository.modify(await self._to_model(entity))
#
#     # An entity should only be removed using this method
#     async def remove(self, uid: UniqueIdentifier):
#         if uid not in self._identity_map:
#             raise EntityNotFoundException(status=400, msg='Entity was not created by this aggregate root')
#         await self._repository.remove(str(uid))
#         del self._identity_map[uid]
#
#     def validate(self, entity: T_Entity) -> bool:
#         return all([
#             entity is not None,
#             isinstance(entity.uid, UniqueIdentifier)
#         ])
#
#     @abc.abstractmethod
#     async def _to_model(self, entity: T_Entity) -> T_EntityModel:
#         pass
#
#     @abc.abstractmethod
#     async def _from_model(self, model: T_EntityModel) -> T_Entity:
#         pass
#
#
# T_AggregateRoot = typing.TypeVar('T_AggregateRoot', bound=AggregateRootOld)
#
#
