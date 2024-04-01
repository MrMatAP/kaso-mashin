import typing
import enum
import pathlib
import subprocess

from pydantic import Field
import jinja2
import jinja2.meta

from sqlalchemy import String, Enum, UnicodeText
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


class BootstrapKind(str, enum.Enum):
    IGNITION = 'ignition'
    CLOUD_INIT = 'cloud-init'


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
    kind: Mapped[BootstrapKind] = mapped_column(Enum(BootstrapKind))
    content: Mapped[str] = mapped_column(UnicodeText)


class BootstrapEntity(Entity, AggregateRoot):
    """
    Domain model entity for bootstrap
    """

    def __init__(self,
                 name: str,
                 kind: BootstrapKind,
                 content: str):
        super().__init__()
        self._name = name
        self._kind = kind
        self._content = content
        self._template = jinja2.Environment(enable_async=True).from_string(self._content)
        ast = jinja2.Environment().parse(self._content)
        self._required_keys = jinja2.meta.find_undeclared_variables(ast)

    @property
    def name(self) -> str:
        return self._name

    @property
    def kind(self) -> BootstrapKind:
        return self._kind

    @property
    def content(self) -> str:
        return self._content

    @property
    def required_keys(self) -> typing.Set:
        return self._required_keys

    async def render(self, kv: typing.Dict[str, typing.Any], bootstrap_file: pathlib.Path):
        try:
            rendered = await self._template.render_async(kv)
            if self.kind == BootstrapKind.IGNITION:
                args = [self.runtime.butane_path, '-p', '-o', bootstrap_file]
                subprocess.run(args, check=True)
            else:
                bootstrap_file.write_text(rendered, encoding='utf-8')
        except jinja2.TemplateError as te:
            raise BootstrapException(status=400, msg='Templating error') from te
        except subprocess.CalledProcessError as e:
            raise BootstrapException(status=500, msg='Failed to render bootstrap') from e

    def __eq__(self, other: 'BootstrapEntity') -> bool:
        return all([
            super().__eq__(other),
            self.name == other.name,
            self.kind == other.kind,
            self.content == other.content
        ])

    def __repr__(self) -> str:
        return (
            f'BootstrapEntity(uid={self.uid}, '
            f'name={self.name},'
            f'kind={self.kind})>'
        )

    @staticmethod
    async def from_model(model: BootstrapModel) -> 'BootstrapEntity':
        bootstrap = BootstrapEntity(name=model.name, kind=BootstrapKind(model.kind), content=model.content)
        bootstrap._uid = model.uid
        return bootstrap

    async def to_model(self, model: BootstrapModel | None = None) -> BootstrapModel:
        if model is None:
            return BootstrapModel(uid=str(self.uid),
                                  name=self.name,
                                  kind=self.kind,
                                  content=self.content)
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.kind = self.kind
            model.content = self.content
            return model

    @staticmethod
    async def create(name: str, kind: BootstrapKind, content: str) -> 'BootstrapEntity':
        bootstrap = BootstrapEntity(name=name, kind=kind, content=content)
        await BootstrapEntity.repository.create(bootstrap)
        return bootstrap

    async def modify(self, name: str, kind=kind, content=content):
        self._name = name
        self._kind = kind
        self._content = content
        await self.repository.modify(self)

    async def remove(self):
        await self.repository.remove(self.uid)


class BootstrapRepository(AsyncRepository[BootstrapEntity, BootstrapModel]):
    pass


class BootstrapListSchema(EntitySchema):
    """
    Schema to list bootstraps
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The bootstrap name', examples=['k8s-master'])
    kind: BootstrapKind = Field(description='The bootstrap kind', examples=[BootstrapKind.IGNITION])


class BootstrapCreateSchema(EntitySchema):
    """
    Schema to create a bootstrap
    """
    name: str = Field(description='The bootstrap name', examples=['k8s-master'])
    kind: BootstrapKind = Field(description='The bootstrap kind', examples=[BootstrapKind.IGNITION])
    content: str = Field(description='The bootstrap content template')


class BootstrapGetSchema(EntitySchema):
    """
    Schema to get a bootstrap
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The bootstrap name', examples=['k8s-master'])
    kind: BootstrapKind = Field(description='The bootstrap kind', examples=[BootstrapKind.IGNITION])
    content: str = Field(description='The bootstrap content template')
    required_keys: typing.List[str] = Field(description='Required keys to render this bootstrap template')


class BootstrapModifySchema(EntitySchema):
    """
    Schema to modify a bootstrap
    """
    name: str = Field(description='The bootstrap name', examples=['k8s-master'])
    kind: BootstrapKind = Field(description='The bootstrap kind', examples=[BootstrapKind.IGNITION])
    content: str = Field(description='The bootstrap content template')
