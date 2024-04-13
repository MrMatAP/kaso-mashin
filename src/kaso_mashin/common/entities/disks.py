import enum
import pathlib
import subprocess

from pydantic import Field

from sqlalchemy import String, Integer, Enum, UUID
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntityNotFoundException,
    EntitySchema,
    EntityModel,
    Entity,
    AggregateRoot,
    AsyncRepository,
    BinarySizedValue, BinaryScale
)

from .images import ImageEntity, ImageGetSchema


class DiskFormat(enum.StrEnum):
    Raw = 'raw'
    QCoW2 = 'qcow2'
    VDI = 'vdi'


class DiskListSchema(EntitySchema):
    """
    Schema to list disks
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The disk name', examples=['root', 'data-1', 'data-2'])


class DiskGetSchema(EntitySchema):
    """
    Schema to get information about a specific disk
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    path: pathlib.Path = Field(description='Path of the disk image on the local filesystem',
                               examples=['/var/kaso/instances/root.qcow2'])
    size: BinarySizedValue = Field(description='Disk size',
                                   examples=[BinarySizedValue(2, BinaryScale.G)])
    disk_format: DiskFormat = Field(description='Disk image file format',
                                    examples=[DiskFormat.QCoW2, DiskFormat.Raw])
    image_uid: UniqueIdentifier | None = Field(description='The image uid on which this disk is based on',
                                               optional=True,
                                               default=None)


class DiskCreateSchema(EntitySchema):
    """
    Schema to create a disk
    """
    name: str = Field(description='Disk name',
                      examples=['root', 'data-1', 'data-2'])
    path: pathlib.Path = Field(description='Path of the disk image on the local filesystem',
                               examples=['/var/kaso/instances/root.qcow2'])
    size: BinarySizedValue = Field(description='Disk size',
                                   examples=[BinarySizedValue(2, BinaryScale.G)])
    disk_format: DiskFormat = Field(description='Disk image file format',
                                    examples=[DiskFormat.QCoW2, DiskFormat.Raw])
    image_uid: UniqueIdentifier = Field(description='The image uid on which this disk is based on',
                                        default=None)


class DiskModifySchema(EntitySchema):
    """
    Schema to modify an existing disk
    """
    size: BinarySizedValue = Field(description='Disk size',
                                   examples=[BinarySizedValue(2, BinaryScale.G)],
                                   optional=True,
                                   default=None)


class DiskException(KasoMashinException):
    """
    Exception for disk-related issues
    """
    pass


class DiskModel(EntityModel):
    """
    Representation of a disk entity in the database
    """
    __tablename__ = 'disks'
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer, default=0)
    size_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    disk_format: Mapped[str] = mapped_column(Enum(DiskFormat), default=DiskFormat.Raw)
    image_uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'),
                                           nullable=True)


class DiskEntity(Entity, AggregateRoot):
    """
    Domain model entity for a disk
    """

    def __init__(self,
                 name: str,
                 path: pathlib.Path,
                 size: BinarySizedValue = BinarySizedValue(2, BinaryScale.G),
                 disk_format: DiskFormat = DiskFormat.Raw,
                 image: ImageEntity | None = None) -> None:
        super().__init__()
        self._name = name
        self._path = path
        self._size = size
        self._disk_format = disk_format
        self._image = image

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def size(self) -> BinarySizedValue:
        return self._size

    @property
    def disk_format(self) -> DiskFormat:
        return self._disk_format

    @property
    def image(self) -> ImageEntity:
        return self._image

    @staticmethod
    async def from_model(model: DiskModel) -> 'DiskEntity':
        entity = DiskEntity(name=model.name,
                            path=pathlib.Path(model.path),
                            size=BinarySizedValue(model.size, model.size_scale),
                            disk_format=model.disk_format)
        entity._uid = UniqueIdentifier(model.uid)
        if model.image_uid is not None:
            entity._image = await ImageEntity.repository.get_by_uid(model.image_uid)
        return entity

    async def to_model(self, model: DiskModel | None = None) -> 'DiskModel':
        if model is None:
            return DiskModel(uid=str(self.uid),
                             name=self.name,
                             path=str(self.path),
                             size=self.size.value,
                             size_scale=self.size.scale,
                             disk_format=self.disk_format,
                             image_uid=str(self.image.uid) if self.image is not None else None)
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.path = str(self.path)
            model.size = self.size.value
            model.size_scale = self.size.scale
            model.disk_format = self.disk_format
            if self.image is not None:
                model.image_uid = str(self.image.uid)
            return model

    def __eq__(self, other: 'DiskEntity') -> bool:  # type: ignore[override]
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._path == other.path,
            self._size == other.size,
            self._disk_format == other.disk_format,
            self._image == other.image
        ])

    def __repr__(self) -> str:
        return (
            f'<DiskEntity(uid={self.uid}, '
            f'name={self.name}, '
            f'path={self.path}, '
            f'size={self.size}, '
            f'disk_format={self.disk_format},'
            f'image={self.image})>')

    @staticmethod
    async def create(name: str,
                     path: pathlib.Path,
                     size: BinarySizedValue = BinarySizedValue(2, BinaryScale.G),
                     disk_format: DiskFormat = DiskFormat.Raw,
                     image: ImageEntity | None = None) -> 'DiskEntity':
        if path.exists():
            raise DiskException(status=400, msg=f'Disk at {path} already exists')
        if image is not None and size < image.min_disk:
            raise DiskException(status=400, msg=f'Disk size is less than image minimum size')
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            args = ['/opt/homebrew/bin/qemu-img',
                    'create',
                    '-f', str(disk_format)]
            if image is not None:
                args.extend(['-F', str(disk_format), '-b', image.path, '-o', 'compat=v3'])
            args.extend([path, str(size)])
            subprocess.run(args, check=True)
            disk = DiskEntity(name=name,
                              path=path,
                              size=size,
                              disk_format=disk_format,
                              image=image)
            return await DiskEntity.repository.create(disk)
        except subprocess.CalledProcessError as e:
            path.unlink(missing_ok=True)
            raise DiskException(status=500, msg=f'Failed to create disk: {e.output}') from e
        except EntityNotFoundException as e:
            path.unlink(missing_ok=True)
            raise DiskException(status=400, msg=f'The provided image does not exist') from e
        except PermissionError as e:
            path.unlink(missing_ok=True)
            raise DiskException(status=400, msg=f'You have no permission to create a disk at path {path}') from e

    async def resize(self, value: BinarySizedValue) -> 'DiskEntity':
        try:
            args = ['/opt/homebrew/bin/qemu-img', 'resize']
            if self.size > value:
                args.append('--shrink')
            args += ['-f', str(self.disk_format), self._path, str(value)]
            subprocess.run(args, check=True)
            self._size = value
            await DiskEntity.repository.modify(self)
            return self
        except subprocess.CalledProcessError as e:
            raise DiskException(status=500, msg=f'Failed to resize disk: {e.output}') from e

    async def modify(self, schema: DiskModifySchema) -> 'DiskEntity':
        if schema.size is not None:
            return await self.resize(schema.size)

    async def remove(self):
        self.path.unlink(missing_ok=True)
        await DiskEntity.repository.remove(self.uid)


class DiskRepository(AsyncRepository[DiskEntity, DiskModel]):
    pass
