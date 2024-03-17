from pydantic import Field

from sqlalchemy import String, Enum, select
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntitySchema,
    EntityModel,
    Entity,
    AggregateRoot,
    AsyncRepository
)


class BootstrapException(KasoMashinException):
    """
    Exception for bootstrap-related issues
    """
    pass


class BootstrapModel(EntityModel):
    """
    Representation of a bootstrap entity in the database
    """
    __tablename__ = "bootstraps"
    name: Mapped[str] = mapped_column(String(64))


class BootstrapEntity(Entity, AggregateRoot):
    """
    Domain model entity for bootstrap
    """

    def __init__(self,
                 name: str):
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, other: 'BootstrapEntity') -> bool:
        return all([
            super().__eq__(other),
            self.name == other.name
        ])

    def __repr__(self) -> str:
        return (
            f'BootstrapEntity(uid={self.uid}, '
            f'name={self.name})>'
        )

    @staticmethod
    async def from_model(model: BootstrapModel) -> 'BootstrapEntity':
        bootstrap = BootstrapEntity(name=model.name)
        bootstrap._uid = model.uid
        return bootstrap

    async def to_model(self, model: BootstrapModel | None = None) -> BootstrapModel:
        if model is None:
            return BootstrapModel(uid=str(self.uid),
                                  name=self.name)
        else:
            model.uid = str(self.uid)
            model.name = self.name
            return model

    @staticmethod
    async def create(name: str):
        bootstrap = BootstrapEntity(name=name)
        await BootstrapEntity.repository.create(bootstrap)

    async def modify(self, name: str):
        self._name = name
        await self.repository.modify(self)

    async def remove(self):
        await self.repository.remove(self.uid)


class BootstrapRepository(AsyncRepository[BootstrapEntity, BootstrapModel]):
    pass


class BootstrapListSchema(EntitySchema):
    """
    Schema to list bootstraps
    """