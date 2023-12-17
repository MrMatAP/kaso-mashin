import typing
import enum

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import pydantic

from kaso_mashin import Base
from kaso_mashin.common.model.relation_tables import instance_to_identities


class IdentityKind(enum.StrEnum):
    PUBKEY = 'pubkey'
    PASSWORD = 'password'


class IdentityBaseSchema(pydantic.BaseModel):
    """
    The common base schema for an identity. It deliberately does not contain generated fields we do not
    allow to be provided when creating an identity
    """
    model_config = pydantic.ConfigDict(from_attributes=True)

    gecos: str | None = pydantic.Field(description='The account GECOS field',
                                       default=None,
                                       examples=['Mr Mat'])
    homedir: str | None = pydantic.Field(description='The home directory of the account if explicitly set',
                                         default=None,
                                         examples=['/home/mrmat'])
    shell: str | None = pydantic.Field(description='The account shell if explicitly set',
                                       default=None,
                                       examples=['/bin/bash'])
    passwd: str | None = pydantic.Field(description='The account password for identities of kind "password"',
                                        default=None,
                                        examples=['secret'])
    pubkey: str | None = pydantic.Field(description='The account authorised public key for identities of kind "pubkey"',
                                        default=None,
                                        examples=['ssh-rsa some-very-long-string'])


class IdentitySchema(IdentityBaseSchema):
    """
    An identity
    """
    identity_id: int = pydantic.Field(description='The unique identity id',
                                      examples=[1])
    name: str = pydantic.Field(description='The identity name, equals the account login on the instance',
                               examples=['mrmat'])
    kind: IdentityKind = pydantic.Field(description='The corresponding account kind',
                                        default=IdentityKind.PUBKEY,
                                        examples=['ssh-rsa some-very-long-string'])


class IdentityCreateSchema(IdentityBaseSchema):
    """
    Input schema for creating an identity
    """
    name: str = pydantic.Field(description='The identity name, equals the account login on the instance')
    kind: IdentityKind = pydantic.Field(description='The corresponding account kind', default=IdentityKind.PUBKEY)


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
    __table_args__ = {'sqlite_autoincrement': True}
    identity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement='auto')
    name: Mapped[str] = mapped_column(String, unique=True)
    kind: Mapped[IdentityKind] = mapped_column(Enum(IdentityKind))

    gecos: Mapped[str] = mapped_column(String, nullable=True)
    homedir: Mapped[str] = mapped_column(String, nullable=True)
    passwd: Mapped[str] = mapped_column(String, nullable=True)
    shell: Mapped[str] = mapped_column(String, nullable=True)
    pubkey: Mapped[str] = mapped_column(String, nullable=True)

    instances: Mapped[typing.List['InstanceModel']] = relationship(secondary=instance_to_identities,
                                                                   back_populates='identities')

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

    def __eq__(self, other) -> bool:
        return all([
            isinstance(other, IdentityModel),
            self.identity_id == other.identity_id,
            self.name == other.name,
            self.kind == other.kind,
            self.gecos == other.gecos,
            self.homedir == other.homedir,
            self.passwd == other.passwd,
            self.shell == other.shell,
            self.pubkey == other.pubkey
        ])

    def __repr__(self) -> str:
        return f'IdentityModel(' \
               f'identity_id={self.identity_id}, ' \
               f'name="{self.name}", ' \
               f'kind="{self.kind}")'
