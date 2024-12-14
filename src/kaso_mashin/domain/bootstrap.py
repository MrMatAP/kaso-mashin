import asyncio
import enum
import pathlib
import shutil
import subprocess
import tempfile
import typing
from typing import Optional, List

import aiofiles
import httpx
import jinja2.meta
import rich.box
import rich.table
from pydantic import Field
from sqlalchemy import String, Enum, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column, relationship

import kaso_mashin.base
from kaso_mashin.base import EntityNotFoundException
from kaso_mashin.services import Task, TaskState, ConfigService
from kaso_mashin.services.config_service import DEFAULT_K8S_MASTER_TEMPLATE_NAME, \
    DEFAULT_K8S_SLAVE_TEMPLATE_NAME


class BootstrapException(kaso_mashin.base.KasoMashinException):
    """
    Exception for bootstrap-related issues
    """
    pass


class BootstrapKind(str, enum.Enum):
    IGNITION = "ignition"
    CLOUD_INIT = "cloud-init"


class BootstrapModel(kaso_mashin.base.Model):
    """
    Representation of a bootstrap entity in the database
    """

    __tablename__ = "bootstraps"
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[BootstrapKind] = mapped_column(Enum(BootstrapKind))
    content: Mapped[str] = mapped_column(UnicodeText)

    instances: Mapped[Optional[List['kaso_mashin.domain.instance.InstanceModel']]] = relationship(
        lazy='selectin', back_populates='bootstrap')


class Bootstrap(kaso_mashin.base.AggregateRoot['BootstrapRepository']):
    """
    Domain model entity for bootstrap
    """

    def __init__(self, name: str, kind: BootstrapKind, content: str):
        super().__init__(name)
        self._kind = kind
        self._content = content
        self._template = jinja2.Environment(enable_async=True).from_string(content)
        ast = jinja2.Environment().parse(self._content)
        self._required_keys = jinja2.meta.find_undeclared_variables(ast)

    @property
    def kind(self) -> BootstrapKind:
        return self._kind

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self._template = jinja2.Environment(enable_async=True).from_string(self._content)
        ast = jinja2.Environment().parse(self._content)
        self._required_keys = jinja2.meta.find_undeclared_variables(ast)
        self._dirty = True

    @property
    def required_keys(self) -> typing.Set:
        return self._required_keys

    async def render(self, kv: typing.Dict[str, typing.Any], bootstrap_file: pathlib.Path):
        try:
            if bootstrap_file.exists():
                raise kaso_mashin.base.EntityInvariantException(status=400,
                                                                msg=f'Bootstrap file at {bootstrap_file} already exists')
            bootstrap_file.parent.mkdir(parents=True, exist_ok=True)

            class ButaneRenderTask(Task):
                async def run(self,
                              path: pathlib.Path,
                              content: str,
                              butane_path: pathlib.Path) -> None:
                    try:
                        await super().run()
                        with tempfile.TemporaryFile(mode='w', encoding='UTF-8') as source:
                            source.write(content)
                            args = [butane_path, '-p', '-o', source, path]
                            subprocess.run(args, check=True)
                        await self.done('Bootstrap successfully rendered via butane')
                    except subprocess.CalledProcessError as e:
                        await self.fail(f'Failed to render via butane: {e.output}')
                    except asyncio.CancelledError:
                        self._state = TaskState.CANCELLED
                        path.unlink(missing_ok=True)

            rendered = await self._template.render_async(kv)
            if self.kind == BootstrapKind.IGNITION:
                t = self.task_service.create(
                    ButaneRenderTask(name=f'Butane render bootstrap {self.name}'),
                    path=bootstrap_file,
                    content=rendered,
                    butane_path=self.config_service.butane_path)
                await t.task
            else:
                bootstrap_file.write_text(rendered, encoding="utf-8")
            await super().post_create()
        except jinja2.TemplateError as te:
            raise BootstrapException(status=400, msg="Templating error") from te

    def __eq__(self, other: "Bootstrap") -> bool:
        return all([
            super().__eq__(other),
            self.name == other.name,
            self.kind == other.kind,
            self.content == other.content])

    async def pre_remove(self) -> None:
        # TODO: Check if we have any instances using this bootstrap
        return await super().pre_remove()


class BootstrapRepository(kaso_mashin.base.Repository[Bootstrap, BootstrapModel]):
    """
    A repository of bootstraps
    """
    entity_class = Bootstrap
    model_class = BootstrapModel

    @classmethod
    async def from_model(cls, model: BootstrapModel, *args, **kwargs) -> Bootstrap:
        kwargs['kind'] = model.kind
        kwargs['content'] = model.content
        return await super().from_model(model, *args, **kwargs)

    @classmethod
    async def to_model(cls, entity: Bootstrap,
                       persisted: BootstrapModel | None = None) -> BootstrapModel:
        model = await super().to_model(entity, persisted)
        model.kind = entity.kind
        model.content = entity.content
        return model

    async def initialise(self):
        await super().initialise()
        client = httpx.AsyncClient(follow_redirects=True, timeout=60, http2=True)
        if not self._config_service.uefi_code_path.exists():
            async with (
                client.stream("GET", url=self._config_service.uefi_code_url) as resp,
                aiofiles.open(self._config_service.uefi_code_path, "wb") as file,
            ):
                async for chunk in resp.aiter_bytes(chunk_size=8196):
                    await file.write(chunk)
            shutil.chown(path=self._config_service.uefi_code_path,
                         user=self._config_service.owning_user)
        if not self._config_service.uefi_vars_path.exists():
            async with (
                client.stream("GET", url=self._config_service.uefi_vars_url) as resp,
                aiofiles.open(self._config_service.uefi_vars_path, "wb") as file,
            ):
                async for chunk in resp.aiter_bytes(chunk_size=8196):
                    await file.write(chunk)
                shutil.chown(path=self._config_service.uefi_vars_path,
                             user=self._config_service.owning_user)
        template_dir = pathlib.Path(__file__).parent.parent / "templates"
        try:
            await self.get_by_name(DEFAULT_K8S_MASTER_TEMPLATE_NAME)
        except EntityNotFoundException:
            ignition_k8s_master_template = template_dir / "ignition_k8s_master.yaml"
            bootstrap = Bootstrap(name=DEFAULT_K8S_MASTER_TEMPLATE_NAME,
                                  kind=BootstrapKind.IGNITION,
                                  content=ignition_k8s_master_template.read_text(encoding="utf-8"))
            await bootstrap.save()
        try:
            await self.get_by_name(DEFAULT_K8S_SLAVE_TEMPLATE_NAME)
        except EntityNotFoundException:
            ignition_k8s_slave_template = template_dir / "ignition_k8s_slave.yaml"
            bootstrap = Bootstrap(name=DEFAULT_K8S_SLAVE_TEMPLATE_NAME,
                                  kind=BootstrapKind.IGNITION,
                                  content=ignition_k8s_slave_template.read_text(encoding="utf-8"))
            await bootstrap.save()


class BootstrapGetSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to get a bootstrap
    """

    uid: kaso_mashin.base.UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="The bootstrap name", examples=["k8s-master"])
    kind: BootstrapKind = Field(description="The bootstrap kind",
                                examples=[BootstrapKind.IGNITION])
    content: str = Field(description="The bootstrap content template")
    required_keys: typing.List[str] = Field(
        description="Required keys to render this bootstrap template"
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Kind", self.kind)
        table.add_row("[blue]Required Keys", ",".join(self.required_keys))
        table.add_row("[blue]Content", self.content)
        return table


class BootstrapListSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to list bootstraps
    """

    entries: typing.List[BootstrapGetSchema] = Field(description="List of bootstraps",
                                                     default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Kind")
        table.add_column("[blue]Name")
        for entry in self.entries:
            table.add_row(str(entry.uid), str(entry.kind.value), entry.name)
        return table


class BootstrapCreateSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to create a bootstrap
    """

    name: str = Field(description="The bootstrap name", examples=["k8s-master"])
    kind: BootstrapKind = Field(description="The bootstrap kind",
                                examples=[BootstrapKind.IGNITION])
    content: str = Field(description="The bootstrap content template")


class BootstrapModifySchema(kaso_mashin.base.EntitySchema):
    """
    Schema to modify a bootstrap
    """

    name: str = Field(description="The bootstrap name", examples=["k8s-master"])
    kind: BootstrapKind = Field(description="The bootstrap kind",
                                examples=[BootstrapKind.IGNITION])
    content: str = Field(description="The bootstrap content template")
