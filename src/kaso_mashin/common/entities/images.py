import typing
import pathlib
import shutil

import aiofiles
import httpx
from pydantic import Field
import rich.table
import rich.box

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntitySchema,
    EntityModel,
    Entity,
    AggregateRoot,
    AsyncRepository,
    BinarySizedValue, BinaryScale
)

from kaso_mashin.common.entities import TaskEntity

DEFAULT_MIN_VCPU = 0
DEFAULT_MIN_RAM = BinarySizedValue(0, BinaryScale.G)
DEFAULT_MIN_DISK = BinarySizedValue(0, BinaryScale.G)


class ImageException(KasoMashinException):
    """
    Exception for image-related issues
    """
    pass


class ImageListEntrySchema(EntitySchema):
    """
    Schema for an image list
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The image name', examples=['ubuntu', 'flatpack', 'debian'])


class ImageListSchema(EntitySchema):
    """
    Schema to list images
    """
    entries: typing.List[ImageListEntrySchema] = Field(description='List of images',
                                                       default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]UID')
        table.add_column('[blue]Name')
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name)
        return table


class ImageCreateSchema(EntitySchema):
    """
    Schema to create an image
    """
    name: str = Field(description='The image name', examples=['ubuntu', 'flatpack', 'debian'])
    url: str = Field(description='URL from which the image is sourced',
                     examples=['https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img'])
    min_vcpu: int = Field(description='Optional minimum number of CPU vcores to run this image',
                          default=DEFAULT_MIN_VCPU,
                          examples=[DEFAULT_MIN_VCPU, 2, 4])
    min_ram: BinarySizedValue = Field(description='Optional minimum RAM size to run this image',
                                      default=DEFAULT_MIN_RAM,
                                      examples=[DEFAULT_MIN_RAM, BinarySizedValue(2, BinaryScale.G)])
    min_disk: BinarySizedValue = Field(description='Optional minimum disk size to run this image',
                                       default=DEFAULT_MIN_DISK,
                                       examples=[DEFAULT_MIN_DISK, BinarySizedValue(10, BinaryScale.G)])


class ImageGetSchema(ImageCreateSchema):
    """
    Schema to get information about a specific image
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    path: pathlib.Path = Field(description='Path to the image on the local disk')

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]UID', str(self.uid))
        table.add_row('[blue]Name', self.name)
        table.add_row('[blue]Path', str(self.path))
        table.add_row('[blue]Min VCPU', str(self.min_vcpu))
        table.add_row('[blue]Min RAM', f'{self.min_ram.value} {self.min_ram.scale}')
        table.add_row('[blue]Min Disk', f'{self.min_disk.value} {self.min_disk.scale}')
        return table


class ImageModifySchema(EntitySchema):
    """
    Schema to modify an existing image
    """
    min_vcpu: int = Field(description='Optional minimum number of CPU vcores to run this image',
                          default=DEFAULT_MIN_VCPU,
                          examples=[DEFAULT_MIN_VCPU, 2, 4])
    min_ram: BinarySizedValue = Field(description='Optional minimum RAM size to run this image',
                                      default=DEFAULT_MIN_RAM,
                                      examples=[DEFAULT_MIN_RAM, BinarySizedValue(2, BinaryScale.G)])
    min_disk: BinarySizedValue = Field(description='Optional minimum disk size to run this image',
                                       default=DEFAULT_MIN_DISK,
                                       examples=[DEFAULT_MIN_DISK, BinarySizedValue(10, BinaryScale.G)])



class ImageModel(EntityModel):
    """
    Representation of an image entity in the database
    """
    __tablename__ = "images"
    name: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String())
    path: Mapped[str] = mapped_column(String())
    min_vcpu: Mapped[int] = mapped_column(Integer, default=0)
    min_ram: Mapped[int] = mapped_column(Integer, default=0)
    min_ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    min_disk: Mapped[int] = mapped_column(Integer, default=0)
    min_disk_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)


class ImageEntity(Entity, AggregateRoot):
    """
    Domain model entity for an image
    """

    def __init__(self,
                 name: str,
                 url: str,
                 path: pathlib.Path,
                 min_vcpu: int = 0,
                 min_ram: BinarySizedValue = BinarySizedValue(0, BinaryScale.G),
                 min_disk: BinarySizedValue = BinarySizedValue(0, BinaryScale.G)):
        super().__init__()
        self._name = name
        self._url = url
        self._path = path
        self._min_vcpu = min_vcpu
        self._min_ram = min_ram
        self._min_disk = min_disk

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._url

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def min_vcpu(self) -> int:
        return self._min_vcpu

    @property
    def min_ram(self) -> BinarySizedValue:
        return self._min_ram

    @property
    def min_disk(self) -> BinarySizedValue:
        return self._min_disk

    def __eq__(self, other: object) -> bool:
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._url == other.url,
            self._path == other.path,
            self._min_vcpu == other.min_vcpu,
            self._min_ram == other.min_ram,
            self._min_disk == other.min_disk
        ])

    def __repr__(self) -> str:
        return (
            f'ImageEntity(uid={self.uid}, '
            f'name={self.name}, '
            f'url={self.url}, '
            f'path={self.path}, '
            f'min_vcpu={self.min_vcpu}, '
            f'min_ram={self.min_ram}, '
            f'min_disk={self.min_disk})'
        )

    @staticmethod
    async def from_model(model: ImageModel) -> 'ImageEntity':
        entity = ImageEntity(name=model.name,
                             url=model.url,
                             path=pathlib.Path(model.path),
                             min_vcpu=model.min_vcpu,
                             min_ram=BinarySizedValue(value=model.min_ram, scale=BinaryScale(model.min_ram_scale)),
                             min_disk=BinarySizedValue(value=model.min_disk, scale=BinaryScale(model.min_disk_scale)))
        entity._uid = UniqueIdentifier(model.uid)
        return entity

    async def to_model(self, model: ImageModel | None = None) -> 'ImageModel':
        if model is None:
            return ImageModel(uid=str(self.uid),
                              name=self.name,
                              url=self.url,
                              path=str(self.path),
                              min_vcpu=self.min_vcpu,
                              min_ram=self.min_ram.value,
                              min_ram_scale=self.min_ram.scale,
                              min_disk=self.min_disk.value,
                              min_disk_scale=self.min_disk.scale)
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.url = self.url
            model.path = str(self.path)
            model.min_vcpu = self.min_vcpu
            model.min_ram = self.min_ram.value
            model.min_ram_scale = self.min_ram.scale
            model.min_disk = self.min_disk.value
            model.min_disk_scale = self.min_disk.scale
            return model

    @staticmethod
    async def create(task: TaskEntity,
                     user: str,
                     name: str,
                     url: str,
                     path: pathlib.Path,
                     min_vcpu: int = DEFAULT_MIN_VCPU,
                     min_ram: BinarySizedValue = DEFAULT_MIN_RAM,
                     min_disk: BinarySizedValue = DEFAULT_MIN_DISK) -> 'ImageEntity':
        if path.exists():
            raise ImageException(status=400, msg=f'Disk at {path} already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            resp = httpx.head(url, follow_redirects=True, timeout=60)
            size = int(resp.headers.get('content-length'))
            current = 0
            client = httpx.AsyncClient(follow_redirects=True, timeout=60)
            async with client.stream('GET', url=url) as resp, aiofiles.open(path, mode='wb') as file:
                async for chunk in resp.aiter_bytes(chunk_size=8196):
                    await file.write(chunk)
                    current += 8196
                    completed = int(current / size * 100)
                    await task.progress(percent_complete=completed, msg=f'Downloaded {completed}%')
            shutil.chown(path, user)
            image = ImageEntity(name=name,
                                url=url,
                                path=path,
                                min_vcpu=min_vcpu,
                                min_ram=min_ram,
                                min_disk=min_disk)
            outcome = await ImageEntity.repository.create(image)
            await task.done(msg='Successfully downloaded')
            return outcome
        except PermissionError as e:
            await task.fail(msg=f'You have no permission to create an image at path {path}')
            raise ImageException(status=400, msg=f'You have no permission to create an image at path {path}') from e
        except Exception as e:
            await task.fail(msg=f'Exception occurred while downloading {e}')
            raise ImageException(status=500, msg=f'Exception occurred while downloading {e}')

    async def modify(self,
                     min_vcpu: int = DEFAULT_MIN_VCPU,
                     min_ram: BinarySizedValue = DEFAULT_MIN_RAM,
                     min_disk: BinarySizedValue = DEFAULT_MIN_DISK):
        self._min_vcpu = min_vcpu
        self._min_ram = min_ram
        self._min_disk = min_disk
        await self.repository.modify(self)

    async def remove(self):
        # TODO: Check for OS disks created here
        # if len(self._os_disks) > 0:
        #     raise EntityInvariantException(status=400, msg=f'You cannot remove an image from which OS disks exists')
        self.path.unlink(missing_ok=True)
        await self.repository.remove(self.uid)


class ImageRepository(AsyncRepository[ImageEntity, ImageModel]):
    pass
