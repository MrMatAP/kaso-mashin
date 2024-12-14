import asyncio
import pathlib
import typing
import datetime
from typing import Optional, List

import aiofiles
import httpx
import rich.box
import rich.table
from pydantic import Field

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

import kaso_mashin
import kaso_mashin.base

from kaso_mashin.services import Task, TaskState
from kaso_mashin.services.config_service import DEFAULT_MIN_VCPU, DEFAULT_MIN_RAM, DEFAULT_MIN_DISK


class ImageException(kaso_mashin.base.KasoMashinException):
    """
    Exception for image-related issues
    """
    pass


class ImageModel(kaso_mashin.base.Model):
    """
    Representation of an image entity in the database
    """

    __tablename__ = "images"
    name: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String())
    path: Mapped[str] = mapped_column(String())
    min_vcpu: Mapped[int] = mapped_column(Integer, default=0)
    min_ram: Mapped[int] = mapped_column(Integer, default=0)
    min_ram_scale: Mapped[str] = mapped_column(Enum(kaso_mashin.base.BinaryScale),
                                               default=kaso_mashin.base.BinaryScale.G)
    min_disk: Mapped[int] = mapped_column(Integer, default=0)
    min_disk_scale: Mapped[str] = mapped_column(Enum(kaso_mashin.base.BinaryScale),
                                                default=kaso_mashin.base.BinaryScale.G)

    disks: Mapped[Optional[List['kaso_mashin.domain.disk.DiskModel']]] = relationship(lazy='selectin', back_populates='image')


class Image(kaso_mashin.base.AggregateRoot['ImageRepository']):
    """
    Domain model entity for an image
    """

    def __init__(
            self,
            name: str,
            url: str):
        super().__init__(name)
        self._url: str = url
        self._min_vcpu: int = 0
        self._min_ram = kaso_mashin.base.BinarySizedValue(value=0,
                                                            scale=kaso_mashin.base.BinaryScale.G)
        self._min_disk = kaso_mashin.base.BinarySizedValue(value=0,
                                                             scale=kaso_mashin.base.BinaryScale.G)
        self._disks: typing.List['kaso_mashin.domain.Disk'] = []
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
        self._path: pathlib.Path = Image.config_service.images_path / f"{name}-{now}.qcow2"

    @property
    def url(self) -> str:
        return self._url

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def min_vcpu(self) -> int:
        return self._min_vcpu

    @min_vcpu.setter
    def min_vcpu(self, value: int) -> None:
        self._min_vcpu = value
        self._dirty = True

    @property
    def min_ram(self) -> kaso_mashin.base.BinarySizedValue:
        return self._min_ram

    @min_ram.setter
    def min_ram(self, value: kaso_mashin.base.BinarySizedValue) -> None:
        self._min_ram = value
        self._dirty = True

    @property
    def min_disk(self) -> kaso_mashin.base.BinarySizedValue:
        return self._min_disk

    @min_disk.setter
    def min_disk(self, value: kaso_mashin.base.BinarySizedValue) -> None:
        self._min_disk = value
        self._dirty = True

    @property
    def disks(self) -> typing.List['kaso_mashin.domain.Disk']:
        return self._disks

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self._url == other.url,
            self._path == other.path,
            self._min_vcpu == other.min_vcpu,
            self._min_ram == other.min_ram,
            self._min_disk == other.min_disk,
            self._disks == other.disks])

    async def save(self, synchronous: bool = True) -> typing.Self | Task:
        """
        Overrides the default save method to enforce asynchronous behaviour
        Args:
            synchronous (): Forced to False

        Returns:
            A task instance
        """
        return await super().save(False)

    async def post_create(self) -> Task:
        try:
            if self.path.exists():
                raise kaso_mashin.base.EntityInvariantException(status=400, msg=f'Image at {self.path} already exists')
            self.path.parent.mkdir(parents=True, exist_ok=True)

            class DownloadTask(Task):
                async def run(self, url: str, path: pathlib.Path):
                    try:
                        await super().run()
                        resp = httpx.head(url, follow_redirects=True, timeout=60)
                        size = int(resp.headers.get('content-length'))
                        client = httpx.AsyncClient(follow_redirects=True, timeout=60)
                        chunk_size = 32784
                        current = 0
                        async with (client.stream('GET', url=url) as resp,
                                    aiofiles.open(path, mode='wb') as image_file):
                            async for chunk in resp.aiter_bytes(chunk_size):
                                await image_file.write(chunk)
                                current += chunk_size
                                await self.progress(int(current / size * 100),
                                                    msg='Downloading image')
                        await self.done('Image downloaded')
                    except asyncio.CancelledError:
                        self._state = TaskState.CANCELLED
                        path.unlink(missing_ok=True)

            t = self.task_service.create(DownloadTask(name=f'Download Image {self.name}'),
                                         callback=lambda: super().post_create,
                                         url=self.url,
                                         path=self.path)

            return t
        except PermissionError as pe:
            raise ImageException(status=400,
                                 msg=f'No permission to save the image at {self.path}') from pe

    async def pre_remove(self) -> None:
        try:
            if len(self.disks) > 0:
                raise kaso_mashin.base.EntityInvariantException(status=400, msg='There are disks using this image as backing store')
            self.path.unlink(missing_ok=True)
            return await super().pre_remove()
        except PermissionError as pe:
            raise ImageException(status=400,
                                 msg=f'No permission to remove the image at {self.path}') from pe


class ImageRepository(kaso_mashin.base.Repository[Image, ImageModel]):
    """
    A repository of images
    """
    entity_class = Image
    model_class = ImageModel

    @classmethod
    async def from_model(cls, model: ImageModel, *args, **kwargs) -> Image:
        kwargs['url'] = model.url
        entity = await super().from_model(model, *args, **kwargs)
        entity.min_vcpu = model.min_vcpu
        entity.min_ram = kaso_mashin.base.BinarySizedValue(value=model.min_ram,
                                                             scale=kaso_mashin.base.BinaryScale(model.min_ram_scale))
        entity.min_disk = kaso_mashin.base.BinarySizedValue(value=model.min_disk,
                                                              scale=kaso_mashin.base.BinaryScale(model.min_disk_scale))
        if model.disks is not None:
            for disk in model.disks:
                entity.disks.append(await kaso_mashin.domain.Disk.repository.get_by_uid(kaso_mashin.base.UniqueIdentifier(disk.uid)))
        entity.dirty = False
        return entity

    @classmethod
    async def to_model(cls, entity: Image, persisted: ImageModel | None = None) -> ImageModel:
        model = await super().to_model(entity, persisted)
        model.url = entity.url
        model.path = str(entity.path)
        model.min_vcpu = entity.min_vcpu
        model.min_ram = entity.min_ram.value
        model.min_ram_scale = entity.min_ram.scale
        model.min_disk = entity.min_disk.value
        model.min_disk_scale = entity.min_disk.scale
        return model


class ImageCreateSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to create an image
    """

    name: str = Field(description="The image name", examples=["ubuntu", "flatpack", "debian"])
    url: str = Field(
        description="URL from which the image is sourced",
        examples=[
            "https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img"
        ],
    )
    min_vcpu: int = Field(
        description="Optional minimum number of CPU vcores to run this image",
        default=DEFAULT_MIN_VCPU,
        examples=[DEFAULT_MIN_VCPU, 2, 4],
    )
    min_ram: kaso_mashin.base.BinarySizedValue = Field(
        description="Optional minimum RAM size to run this image",
        default=DEFAULT_MIN_RAM,
        examples=[DEFAULT_MIN_RAM, kaso_mashin.base.BinarySizedValue(value=2,
                                                                     scale=kaso_mashin.base.BinaryScale.G)],
    )
    min_disk: kaso_mashin.base.BinarySizedValue = Field(
        description="Optional minimum disk size to run this image",
        default=DEFAULT_MIN_DISK,
        examples=[DEFAULT_MIN_DISK, kaso_mashin.base.BinarySizedValue(value=10,
                                                                      scale=kaso_mashin.base.BinaryScale.G)],
    )


class ImageGetSchema(ImageCreateSchema):
    """
    Schema to get information about a specific image
    """

    uid: kaso_mashin.base.UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    path: pathlib.Path = Field(description="Path to the image on the local disk")

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Path", str(self.path))
        table.add_row("[blue]Min VCPU", str(self.min_vcpu))
        table.add_row("[blue]Min RAM", f"{self.min_ram.value} {self.min_ram.scale}")
        table.add_row("[blue]Min Disk", f"{self.min_disk.value} {self.min_disk.scale}")
        return table


class ImageListSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to list images
    """

    entries: typing.List[ImageGetSchema] = Field(description="List of images", default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Name")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name)
        return table


class ImageModifySchema(kaso_mashin.base.EntitySchema):
    """
    Schema to modify an existing image
    """

    name: typing.Optional[str] = Field(
        description="The image name", examples=["ubuntu", "flatpack", "debian"]
    )
    min_vcpu: typing.Optional[int] = Field(
        description="Optional minimum number of CPU vcores to run this image",
        default=DEFAULT_MIN_VCPU,
        examples=[DEFAULT_MIN_VCPU, 2, 4],
    )
    min_ram: typing.Optional[kaso_mashin.base.BinarySizedValue] = Field(
        description="Optional minimum RAM size to run this image",
        default=DEFAULT_MIN_RAM,
        examples=[DEFAULT_MIN_RAM, kaso_mashin.base.BinarySizedValue(2, kaso_mashin.base.BinaryScale.G)],
    )
    min_disk: typing.Optional[kaso_mashin.base.BinarySizedValue] = Field(
        description="Optional minimum disk size to run this image",
        default=DEFAULT_MIN_DISK,
        examples=[DEFAULT_MIN_DISK, kaso_mashin.base.BinarySizedValue(10, kaso_mashin.base.BinaryScale.G)],
    )
