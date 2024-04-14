import typing
import enum
import pathlib

from pydantic import Field
import rich.table
import rich.box

from sqlalchemy import String, Enum
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


class IdentityKind(enum.StrEnum):
    PUBKEY = 'pubkey'
    PASSWORD = 'password'


class IdentityException(KasoMashinException):
    """
    Exception for identity-related issues
    """
    pass


class IdentityListEntrySchema(EntitySchema):
    """
    Schema for a identity list
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The identity name', examples=['imfeldma'])
    kind: IdentityKind = Field(description='The identity kind')
    gecos: str = Field(description='The identity GECOS')


class IdentityListSchema(EntitySchema):
    """
    Schema to list identities
    """
    entries: typing.List[IdentityListEntrySchema] = Field(description='List of identities',
                                                          default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]UID')
        table.add_column('[blue]Kind')
        table.add_column('[blue]Name')
        table.add_column('[blue]Gecos')
        for entry in self.entries:
            table.add_row(str(entry.uid),
                          str(entry.kind.value),
                          entry.name,
                          entry.gecos)
        return table


class IdentityGetSchema(EntitySchema):
    """
    Schema to get identities
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The identity name', examples=['imfeldma'])
    kind: IdentityKind = Field(description='The identity kind')
    gecos: str = Field(description='The identity GECOS')
    homedir: pathlib.Path = Field(description='The home directory')
    shell: str = Field(description='The identity shell')
    credential: str = Field(description='The identity credential')
    
    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]UID', str(self.uid))
        table.add_row('[blue]Name', self.name)
        table.add_row('[blue]Kind', self.kind)
        table.add_row('[blue]GECOS', self.gecos or '')
        table.add_row('[blue]Home Directory', str(self.homedir) or '')
        table.add_row('[blue]Shell', self.shell or '')
        table.add_row('[blue]Credential', self.credential or '')
        return table


class IdentityCreateSchema(EntitySchema):
    """
    Schema to create an identity
    """
    name: str = Field(description='The identity name', examples=['imfeldma'])
    kind: IdentityKind = Field(description='The identity kind')
    gecos: str = Field(description='The identity GECOS')
    homedir: pathlib.Path = Field(description='The home directory')
    shell: str = Field(description='The identity shell')
    credential: str = Field(description='The identity credential')


class IdentityModifySchema(EntitySchema):
    """
    Schema to modify an identity
    """
    name: str = Field(description='The identity name', examples=['imfeldma'], optional=True, default=None)
    kind: IdentityKind = Field(description='The identity kind', optional=True, default=None)
    gecos: str = Field(description='The identity GECOS', optional=True, default=None)
    homedir: pathlib.Path = Field(description='The home directory', optional=True, default=None)
    shell: str = Field(description='The identity shell', optional=True, default=None)
    credential: str = Field(description='The identity credential', optional=True, default=None)


class IdentityModel(EntityModel):
    """
    Representation of an identity entity in the database
    """
    __tablename__ = 'identities'
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[IdentityKind] = mapped_column(Enum(IdentityKind))
    gecos: Mapped[str] = mapped_column(String, nullable=True)
    homedir: Mapped[str] = mapped_column(String, nullable=True)
    shell: Mapped[str] = mapped_column(String, nullable=True)
    credential: Mapped[str] = mapped_column(String, nullable=True)


class IdentityEntity(Entity, AggregateRoot):
    """
    Domain model entity for an identity
    """

    def __init__(self,
                 name: str,
                 kind: IdentityKind = IdentityKind.PUBKEY,
                 gecos: str = None,
                 homedir: pathlib.Path = None,
                 shell: str = '/bin/bash',
                 credential: str = None):
        super().__init__()
        self._name = name
        self._kind = kind
        self._gecos = gecos
        self._homedir = homedir
        self._shell = shell
        self._credential = credential

    @property
    def name(self) -> str:
        return self._name

    @property
    def kind(self) -> IdentityKind:
        return self._kind

    @property
    def gecos(self) -> str:
        return self._gecos

    @property
    def homedir(self) -> pathlib.Path:
        return self._homedir

    @property
    def shell(self) -> str:
        return self._shell

    @property
    def credential(self) -> str:
        return self._credential

    @staticmethod
    async def from_model(model: IdentityModel) -> 'IdentityEntity':
        entity = IdentityEntity(name=model.name,
                                kind=model.kind,
                                gecos=model.gecos,
                                homedir=pathlib.Path(model.homedir),
                                shell=model.shell,
                                credential=model.credential)
        entity._uid = UniqueIdentifier(model.uid)
        return entity

    async def to_model(self, model: IdentityModel | None = None) -> IdentityModel:
        if model is None:
            return IdentityModel(uid=str(self.uid),
                                 name=self.name,
                                 kind=self.kind,
                                 gecos=self.gecos,
                                 homedir=str(self.homedir),
                                 shell=self.shell,
                                 credential=self.credential)
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.kind = self.kind
            model.gecos = self.gecos
            model.homedir = str(self.homedir)
            model.shell = self.shell
            model.credential = self.credential
            return model

    def __eq__(self, other: 'IdentityEntity') -> bool:
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._kind == other.kind,
            self._gecos == other.gecos,
            self._homedir == other.homedir,
            self._shell == other.shell,
            self._credential == other.credential
        ])

    def __repr__(self) -> str:
        return (
            f'IdentityEntity(uid={self.uid}, '
            f'name={self.name}, '
            f'kind={self.kind}, '
            f'gecos={self.gecos}, '
            f'homedir={self.homedir}, '
            f'shell={self.shell}'
            ')')

    @staticmethod
    async def create(name: str,
                     kind: IdentityKind,
                     gecos: str,
                     homedir: pathlib.Path,
                     shell: shell,
                     credential: str):
        identity = IdentityEntity(name=name,
                                  kind=kind,
                                  gecos=gecos,
                                  homedir=homedir,
                                  shell=shell,
                                  credential=credential)
        return await IdentityEntity.repository.create(identity)

    async def modify(self, schema: IdentityModifySchema) -> 'IdentityEntity':
        if schema.name is not None:
            self._name = schema.name
        if schema.kind is not None:
            self._kind = schema.kind
        if schema.gecos is not None:
            self._gecos = schema.gecos
        if schema.homedir is not None:
            self._homedir = schema.homedir
        if schema.shell is not None:
            self._shell = schema.shell
        if schema.credential is not None:
            self._credential = schema.credential
        return await IdentityEntity.repository.modify(self)

    async def remove(self):
        await IdentityEntity.repository.remove(self.uid)


class IdentityRepository(AsyncRepository[IdentityEntity, IdentityModel]):
    pass
