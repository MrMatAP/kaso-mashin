import pathlib
import shutil

import aiofiles
import httpx
from pydantic import Field

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kaso_mashin import KasoMashinException
from kaso_mashin.common.base_types import (
    ORMBase, SchemaBase,
    Entity, AggregateRoot,
    BinarySizedValue, BinaryScale,
    UniqueIdentifier, T_Model
)

from kaso_mashin.common.entities import TaskState, TaskEntity

DEFAULT_MIN_VCPU = 0
DEFAULT_MIN_RAM = BinarySizedValue(0, BinaryScale.G)
DEFAULT_MIN_DISK = BinarySizedValue(0, BinaryScale.G)


class ImageException(KasoMashinException):
    """
    Exception for image-related issues
    """
    pass


class ImageModel(ORMBase):
    """
    Representation of a image entity in the database
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
    #os_disks: Mapped[typing.List[DiskModel]] = relationship()

    def merge(self, other: 'ImageModel'):
        self.name = other.name
        self.url = other.url
        self.path = other.path
        self.min_vcpu = other.min_vcpu
        self.min_ram = other.min_ram
        self.min_ram_scale = other.min_ram_scale
        self.min_disk = other.min_disk
        self.min_disk_scale = other.min_disk_scale


class ImageListSchema(SchemaBase):
    """
    Schema to list images
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The image name', examples=['ubuntu', 'flatpack', 'debian'])


class ImageCreateSchema(SchemaBase):
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


class ImageModifySchema(SchemaBase):
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


class ImageEntity(Entity):
    """
    Domain model entity for an image
    """

    def __init__(self,
                 owner: 'ImageAggregateRoot',
                 name: str,
                 url: str,
                 path: pathlib.Path,
                 min_vcpu: int = 0,
                 min_ram: BinarySizedValue = BinarySizedValue(0, BinaryScale.G),
                 min_disk: BinarySizedValue = BinarySizedValue(0, BinaryScale.G)) -> None:
        super().__init__(owner=owner)
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

    def __eq__(self, other: 'ImageEntity') -> bool:
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
            f'<ImageEntity(uid={self.uid}, '
            f'name={self.name}, '
            f'url={self.url}, '
            f'path={self.path}, '
            f'min_vcpu={self.min_vcpu}, '
            f'min_ram={self.min_ram}, '
            f'min_disk={self.min_disk})>'
        )

    @staticmethod
    async def create(owner: 'ImageAggregateRoot',
                     task: TaskEntity,
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
            image = ImageEntity(owner=owner,
                                name=name,
                                url=url,
                                path=path,
                                min_vcpu=min_vcpu,
                                min_ram=min_ram,
                                min_disk=min_disk)
            outcome = await owner.create(image)
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
        await self.owner.modify(self)

    async def remove(self):
        # TODO: Check whether we have any disks associated with this image
        self.path.unlink(missing_ok=True)
        await self._owner.remove(self.uid)


class ImageAggregateRoot(AggregateRoot[ImageEntity, ImageModel]):

    def _validate(self, entity: ImageEntity) -> bool:
        return all([
            super().validate(entity),
            entity.path.exists()
        ])

    def _to_model(self, entity: ImageEntity) -> ImageModel:
        return ImageModel(uid=str(entity.uid),
                          name=entity.name,
                          url=entity.url,
                          path=str(entity.path),
                          min_vcpu=entity.min_vcpu,
                          min_ram=entity.min_ram.value,
                          min_ram_scale=entity.min_ram.scale,
                          min_disk=entity.min_disk.value,
                          min_disk_scale=entity.min_disk.scale)

    def _from_model(self, model: T_Model) -> ImageEntity:
        entity = ImageEntity(owner=self,
                             name=model.name,
                             url=model.url,
                             path=pathlib.Path(model.path),
                             min_vcpu=model.min_vcpu,
                             min_ram=BinarySizedValue(model.min_ram, BinaryScale(model.min_ram_scale)),
                             min_disk=BinarySizedValue(model.min_disk, BinaryScale(model.min_disk_scale)))
        entity._uid = UniqueIdentifier(model.uid)
        return entity
