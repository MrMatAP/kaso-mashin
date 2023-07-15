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
    gecos: str | None = pydantic.Field(title='The account GECOS field', default=None)
    homedir: str | None = pydantic.Field(title='The home directory of the account if explicitly set', default=None)
    shell: str | None = pydantic.Field(title='The account shell if explicitly set', default=None)
    passwd: str | None = pydantic.Field(title='The account password for identities of kind "password"', default=None)
    pubkey: str | None = pydantic.Field(title='The account authorised public key for identities of kind "pubkey"', default=None)

    model_config = pydantic.ConfigDict(from_attributes=True)


class IdentitySchema(IdentityBaseSchema):
    """
    An identity
    """
    identity_id: int = pydantic.Field(description='The unique identity id')
    name: str = pydantic.Field(description='The identity name, equals the account login on the instance')
    kind: IdentityKind = pydantic.Field(description='The corresponding account kind', default=IdentityKind.PUBKEY.value)


class IdentityCreateSchema(IdentityBaseSchema):
    """
    Input schema for creating an identity
    """
    name: str = pydantic.Field(description='The identity name, equals the account login on the instance')
    kind: IdentityKind = pydantic.Field(description='The corresponding account kind', default=IdentityKind.PUBKEY.value)


class IdentityModifySchema(IdentityBaseSchema):
    """
    Input schema for modifying an identity
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

    gecos: Mapped[str] = mapped_column(String, nullable=True)
    homedir: Mapped[str] = mapped_column(String, nullable=True)
    passwd: Mapped[str] = mapped_column(String, nullable=True)
    shell: Mapped[str] = mapped_column(String, nullable=True)
    pubkey: Mapped[str] = mapped_column(String, nullable=True)

    @staticmethod
    def from_schema(schema: IdentityCreateSchema | IdentityModifySchema) -> 'IdentityModel':
        model = IdentityModel(
            gecos=schema.gecos,
            homedir=schema.homedir,
            passwd=schema.passwd,
            shell=schema.shell,
            pubkey=schema.pubkey)
        if isinstance(schema, IdentityCreateSchema):
            model.name = schema.name
            model.kind = schema.kind
        return model

    def __repr__(self) -> str:
        return f'IdentityModel(' \
               f'identity_id={self.identity_id}, ' \
               f'name="{self.name}", ' \
               f'kind="{self.kind}")'
