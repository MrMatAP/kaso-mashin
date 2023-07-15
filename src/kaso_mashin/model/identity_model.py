import enum

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
import pydantic

from kaso_mashin import Base


class IdentityBaseSchema(pydantic.BaseModel):
    """
    The common base schema for an identity. It deliberately does not contain generated fields we do not
    allow to be provided when creating an identity
    """
    name: str = pydantic.Field(description='The identity name')
    kind: str = pydantic.Field(description='The corresponding account kind')
    credentials: str = pydantic.Field(description='The account credentials')


class IdentitySchema(IdentityBaseSchema):
    """
    The identity as it is being returned
    """
    pass

class IdentityCreateSchema(IdentityBaseSchema):
    """
    Input schema for creating an identity
    """
    pass


class IdentityKind(enum.Enum):
    PUBKEY = 'pubkey'
    PASSWORD = 'password'


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
