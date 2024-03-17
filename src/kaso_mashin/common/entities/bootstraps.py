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
