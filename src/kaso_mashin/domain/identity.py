import enum
import pathlib
import typing

import rich.box
import rich.table

from pydantic import Field
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column

import kaso_mashin.base


class IdentityException(kaso_mashin.base.KasoMashinException):
    """
    Exception for identity-related issues
    """
    pass


class IdentityKind(enum.StrEnum):
    PUBKEY = "pubkey"
    PASSWORD = "password"


class IdentityModel(kaso_mashin.base.Model):
    """
    Representation of an identity entity in the database
    """

    __tablename__ = "identities"
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[IdentityKind] = mapped_column(Enum(IdentityKind))
    gecos: Mapped[str] = mapped_column(String, nullable=True)
    homedir: Mapped[str] = mapped_column(String, nullable=True)
    shell: Mapped[str] = mapped_column(String, nullable=True)
    credential: Mapped[str] = mapped_column(String, nullable=True)


class Identity(kaso_mashin.base.AggregateRoot['IdentityRepository']):
    """
    Domain model entity for an identity
    """

    def __init__(self, name: str, kind: IdentityKind = IdentityKind.PUBKEY):
        super().__init__(name)
        self._kind = kind
        self._gecos: str = 'Someone'
        self._homedir: pathlib.Path = pathlib.Path(f'/home/{name.replace(" ", "_")}')
        self._shell: str = '/bin/bash'
        self._credential: str = ''

    @property
    def kind(self) -> IdentityKind:
        return self._kind

    @property
    def gecos(self) -> str:
        return self._gecos

    @gecos.setter
    def gecos(self, value: str) -> None:
        self._gecos = value
        self._dirty = True

    @property
    def homedir(self) -> pathlib.Path:
        return self._homedir

    @homedir.setter
    def homedir(self, value: pathlib.Path) -> None:
        self._homedir = value
        self._dirty = True

    @property
    def shell(self) -> str:
        return self._shell

    @shell.setter
    def shell(self, value: str) -> None:
        self._shell = value
        self._dirty = True

    @property
    def credential(self) -> str:
        return self._credential

    @credential.setter
    def credential(self, value: str) -> None:
        self._credential = value
        self._dirty = True

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self.kind == other.kind,
            self.gecos == other.gecos,
            self.homedir == other.homedir,
            self.shell == other.shell,
            self.credential == other.credential])


class IdentityRepository(kaso_mashin.base.Repository[Identity, IdentityModel]):
    """
    A repository of identities
    """
    entity_class = Identity
    model_class = IdentityModel

    @classmethod
    async def from_model(cls, model: IdentityModel, *args, **kwargs) -> Identity:
        kwargs['kind'] = model.kind
        entity = await super().from_model(model, *args, **kwargs)
        entity.gecos = model.gecos
        entity.homedir = pathlib.Path(model.homedir)
        entity.shell = model.shell
        entity.credential = model.credential
        entity.dirty = False
        return entity

    @classmethod
    async def to_model(cls, entity: Identity, persisted: IdentityModel | None = None) -> IdentityModel:
        model = await super().to_model(entity, persisted)
        model.kind = entity.kind
        model.gecos = entity.gecos
        model.homedir = str(entity.homedir)
        model.shell = entity.shell
        model.credential = entity.credential
        return model


class IdentityCreateSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to create an identity
    """

    name: str = Field(description="The identity name", examples=["imfeldma"])
    kind: IdentityKind = Field(description="The identity kind")
    gecos: str = Field(description="The identity GECOS")
    homedir: pathlib.Path = Field(description="The home directory")
    shell: str = Field(description="The identity shell")
    credential: str = Field(description="The identity credential")


class IdentityGetSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to get identities
    """

    uid: kaso_mashin.base.UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="The identity name", examples=["imfeldma"])
    kind: IdentityKind = Field(description="The identity kind")
    gecos: str = Field(description="The identity GECOS")
    homedir: pathlib.Path = Field(description="The home directory")
    shell: str = Field(description="The identity shell")
    credential: str = Field(description="The identity credential")

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Kind", self.kind)
        table.add_row("[blue]GECOS", self.gecos or "")
        table.add_row("[blue]Home Directory", str(self.homedir) or "")
        table.add_row("[blue]Shell", self.shell or "")
        table.add_row("[blue]Credential", self.credential or "")
        return table


class IdentityListSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to list identities
    """

    entries: typing.List[IdentityGetSchema] = Field(
        description="List of identities", default_factory=list
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Kind")
        table.add_column("[blue]Name")
        table.add_column("[blue]Gecos")
        for entry in self.entries:
            table.add_row(str(entry.uid), str(entry.kind.value), entry.name, entry.gecos)
        return table


class IdentityModifySchema(kaso_mashin.base.EntitySchema):
    """
    Schema to modify an identity
    """

    name: str = Field(
        description="The identity name",
        examples=["imfeldma"],
        optional=True,
        default=None,
    )
    kind: IdentityKind = Field(description="The identity kind", optional=True, default=None)
    gecos: str = Field(description="The identity GECOS", optional=True, default=None)
    homedir: pathlib.Path = Field(description="The home directory", optional=True, default=None)
    shell: str = Field(description="The identity shell", optional=True, default=None)
    credential: str = Field(description="The identity credential", optional=True, default=None)
