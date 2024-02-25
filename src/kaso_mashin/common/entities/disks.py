import typing
import pathlib
import subprocess

from pydantic import Field, BaseModel

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin.common.base_types import (
    KasoMashinException,
    ORMBase, SchemaBase,
    Entity, AggregateRoot,
    T_Schema,
    BinarySizedValue,
    UniqueIdentifier, BinaryScale, DiskFormat)


class DiskException(KasoMashinException):
    pass


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

    def merge(self, other: 'DiskModel'):
        self.name = other.name
        self.path = other.path
        self.size = other.size
        self.size_scale = other.size_scale
        self.format = other.format


class DiskListSchema(SchemaBase):
    name: str = Field(description='The disk name', examples=['root', 'data-1', 'data-2'])


class DiskGetSchema(SchemaBase):
    name: str = Field(description='Disk name',
                      examples=['root', 'data-1', 'data-2'])
    path: pathlib.Path = Field(description='Path of the disk image on the local filesystem',
                               examples=['/var/kaso/instances/root.qcow2'])
    size: BinarySizedValue = Field(description='Disk size')
    disk_format: DiskFormat = Field(description='Disk image file format')


class DiskCreateSchema(BaseModel):
    name: str = Field(description='Disk name',
                      examples=['root', 'data-1', 'data-2'])
    path: pathlib.Path = Field(description='Path of the disk image on the local filesystem',
                               examples=['/var/kaso/instances/root.qcow2'])
    size: BinarySizedValue = Field(description='Disk size')
    disk_format: DiskFormat = Field(description='Disk image file format')


class DiskModifySchema(BaseModel):
    size: BinarySizedValue = Field(description='Disk size')


class DiskEntity(Entity):
    """
    Domain model entity for a disk
    """

    def __init__(self,
                 owner: 'DiskAggregateRoot',
                 name: str,
                 path: pathlib.Path,
                 size: BinarySizedValue = BinarySizedValue(2, BinaryScale.G),
                 disk_format: DiskFormat = DiskFormat.Raw) -> None:
        super().__init__(owner=owner)
        self._name = name
        self._path = path
        self._size = size
        self._disk_format = disk_format

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

    def __eq__(self, other: 'DiskEntity') -> bool:  # type: ignore[override]
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._path == other.path,
            self._size == other.size,
            self._disk_format == other.disk_format])

    def __repr__(self) -> str:
        return (f'<DiskEntity(uid={self.uid}, '
                f'name={self.name}, '
                f'path={self.path}, '
                f'size={self.size}, '
                f'disk_format={self.disk_format})>')

    @staticmethod
    async def create(owner: 'DiskAggregateRoot',
                     name: str,
                     path: pathlib.Path,
                     size: BinarySizedValue = BinarySizedValue(2, BinaryScale.G),
                     disk_format: DiskFormat = DiskFormat.Raw) -> 'DiskEntity':
        if path.exists():
            raise DiskException(code=400, msg=f'Disk at {path} already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            disk = DiskEntity(owner=owner,
                              name=name,
                              path=path,
                              size=size,
                              disk_format=disk_format)
            subprocess.run(['/opt/homebrew/bin/qemu-img',
                            'create',
                            '-f', str(disk_format),
                            path,
                            str(size)],
                           check=True)
            return await owner.create(disk)
        except subprocess.CalledProcessError as e:
            path.unlink(missing_ok=True)
            raise DiskException(code=500, msg=f'Failed to create disk: {e.output}') from e

    @staticmethod
    async def schema_create(owner: 'DiskAggregateRoot', schema: DiskCreateSchema) -> 'DiskEntity':
        return await DiskEntity.create(owner=owner,
                                       name=schema.name,
                                       path=pathlib.Path(schema.path),
                                       size=schema.size,
                                       disk_format=schema.disk_format)

    def schema_get(self) -> DiskGetSchema:
        return DiskGetSchema.model_validate(self)

    async def schema_modify(self, schema: DiskModifySchema) -> 'DiskEntity':
        if schema.size != self.size:
            await self.resize(schema.size)
        return self

    async def resize(self, value: BinarySizedValue):
        try:
            subprocess.run(['/opt/homebrew/bin/qemu-img',
                            'resize',
                            '-f', str(self.disk_format),
                            self.path,
                            str(value)],
                           check=True)
            self._size = value
            await self._owner.modify(self)
        except subprocess.CalledProcessError as e:
            raise DiskException(code=500, msg=f'Failed to resize disk: {e.output}') from e

    async def remove(self):
        self.path.unlink(missing_ok=True)
        await self._owner.remove(self.uid)


class DiskAggregateRoot(AggregateRoot[DiskEntity, DiskModel, DiskListSchema]):

    def _validate(self, entity: DiskEntity) -> bool:
        return all([
            super().validate(entity),
            entity.path.exists()
        ])

    def _to_model(self, entity: DiskEntity) -> DiskModel:
        return DiskModel(uid=str(entity.uid),
                         name=entity.name,
                         path=str(entity.path),
                         size=entity.size.value,
                         size_scale=entity.size.scale,
                         format=str(entity.disk_format))

    def _from_model(self, model: DiskModel) -> 'DiskEntity':
        entity = DiskEntity(owner=self,
                            name=model.name,
                            path=pathlib.Path(model.path),
                            size=BinarySizedValue(model.size, BinaryScale(model.size_scale)),
                            disk_format=DiskFormat(model.format))
        entity._uid = UniqueIdentifier(model.uid)
        return entity

    async def list_schema(self) -> typing.List[DiskListSchema]:
        disks = await self.list(force_reload=True)
        return [DiskListSchema.model_validate(disk) for disk in disks]
