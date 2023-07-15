import enum

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
import pydantic

from kaso_mashin import Base


class IdentityKind(enum.Enum):
    PUBKEY = 'pubkey'
    PASSWORD = 'password'


class IdentityBaseSchema(pydantic.BaseModel):
    """
    The common base schema for an identity. It deliberately does not contain generated fields we do not
    allow to be provided when creating an identity
    """
    name: str = pydantic.Field(description='The identity name')
    kind: str = pydantic.Field(description='The corresponding account kind')
    credentials: IdentityKind = pydantic.Field(description='The account credentials', default=IdentityKind.PUBKEY)

    class Config:
        from_attributes = True


class IdentitySchema(IdentityBaseSchema):
    """
    An identity
    """
    pass


class IdentityCreateSchema(IdentityBaseSchema):
    """
    Input schema for creating an identity
    """
    pass


class IdentityModel(Base):
    """
    Representation of an identity in the database
    """

    __tablename__ = 'identities'
    identity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    kind: Mapped[IdentityKind] = mapped_column(Enum(IdentityKind))

    credentials: Mapped[str] = mapped_column(String)

    def __repr__(self) -> str:
        return f'IdentityModel(identity_id={self.identity_id}, ' \
               f'name="{self.name}", ' \
               f'kind="{self.kind}", ' \
               f'credentials=**MASKED**)'
