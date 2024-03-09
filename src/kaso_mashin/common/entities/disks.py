import typing
import enum
import pathlib
import subprocess

from pydantic import Field

from sqlalchemy import String, Integer, Enum, UUID
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import KasoMashinException
from kaso_mashin.common.base_types import (
    ORMBase, SchemaBase,
    Entity, AggregateRoot,
    BinarySizedValue,
    UniqueIdentifier, BinaryScale,
    EntityNotFoundException
)

from .images import ImageEntity, ImageGetSchema


class DiskException(KasoMashinException):
    pass


class DiskFormat(enum.StrEnum):
    Raw = 'raw'
    QCoW2 = 'qcow2'
    VDI = 'vdi'


class DiskModel(ORMBase):
    """
    Representation of a disk entity in the database
    """
    __tablename__ = 'disks'
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer, default=0)
    size_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    format: Mapped[str] = mapped_column(Enum(DiskFormat), default=DiskFormat.Raw)
    image_uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), 'sqlite'),
                                           nullable=True)

    def merge(self, other: 'DiskModel'):
        self.name = other.name
        self.path = other.path
        self.size = other.size
        self.size_scale = other.size_scale
        self.format = other.format


class DiskListSchema(SchemaBase):
    """
    Schema to list disks
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The disk name', examples=['root', 'data-1', 'data-2'])


class DiskCreateSchema(SchemaBase):
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


class DiskGetSchema(SchemaBase):
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
    image: ImageGetSchema = Field(description='The image on which this disk is based on',
                                  default=None)


class DiskModifySchema(SchemaBase):
    """
    Schema to modify an existing disk
    """
    size: BinarySizedValue = Field(description='Disk size',
                                   examples=[BinarySizedValue(2, BinaryScale.G)])


class DiskEntity(Entity):
    """
    Domain model entity for a disk
    """

    def __init__(self,
                 owner: 'DiskAggregateRoot',
                 name: str,
                 path: pathlib.Path,
                 size: BinarySizedValue = BinarySizedValue(2, BinaryScale.G),
                 disk_format: DiskFormat = DiskFormat.Raw,
                 image: ImageEntity | None = None) -> None:
        super().__init__(owner=owner)
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
    async def create(owner: 'DiskAggregateRoot',
                     name: str,
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
            disk = DiskEntity(owner=owner,
                              name=name,
                              path=path,
                              size=size,
                              disk_format=disk_format,
                              image=image)
            return await owner.create(disk)
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
            await self._owner.modify(self)
            return self
        except subprocess.CalledProcessError as e:
            raise DiskException(status=500, msg=f'Failed to resize disk: {e.output}') from e

    async def remove(self):
        self.path.unlink(missing_ok=True)
        await self._owner.remove(self.uid)


class DiskAggregateRoot(AggregateRoot[DiskEntity, DiskModel]):

    def _validate(self, entity: DiskEntity) -> bool:
        return all([
            super().validate(entity),
            entity.path.exists()
        ])

    async def _to_model(self, entity: DiskEntity) -> DiskModel:
        return DiskModel(uid=str(entity.uid),
                         name=entity.name,
                         path=str(entity.path),
                         size=entity.size.value,
                         size_scale=entity.size.scale,
                         format=str(entity.disk_format),
                         image_uid=str(entity.image.uid))

    async def _from_model(self, model: DiskModel) -> DiskEntity:
        image = None
        if model.image_uid is not None:
            image = await self._runtime.image_aggregate_root.get(UniqueIdentifier(str(model.image_uid)))
        entity = DiskEntity(owner=self,
                            name=model.name,
                            path=pathlib.Path(model.path),
                            size=BinarySizedValue(model.size, BinaryScale(model.size_scale)),
                            disk_format=DiskFormat(model.format),
                            image=image)
        entity._uid = UniqueIdentifier(model.uid)
        return entity

    async def list_by_image_uid(self, image_uid: UniqueIdentifier) -> typing.List[DiskEntity]:
        # Force a reload
        disks = self._repository.list()


        # TODO: This is really inefficient and infinitely recursing
        disks = await self._repository.list()
        image_disks = list(filter(lambda d: d.image_uid == image_uid, disks))
        return [await self._from_model(d) for d in image_disks]
