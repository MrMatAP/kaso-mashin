import asyncio
import enum
import pathlib
import subprocess
import typing
from typing import Optional

import rich.box
import rich.table

from pydantic import Field
from sqlalchemy import String, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

import kaso_mashin
import kaso_mashin.base
import kaso_mashin.domain.image

from kaso_mashin.services import Task, TaskState


class DiskException(kaso_mashin.base.KasoMashinException):
    """
    Exception for disk-related issues
    """
    pass


class DiskFormat(enum.StrEnum):
    Raw = "raw"
    QCoW2 = "qcow2"
    VDI = "vdi"


class DiskModel(kaso_mashin.base.Model):
    """
    Representation of a disk entity in the database
    """

    __tablename__ = "disks"
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer, default=0)
    size_scale: Mapped[str] = mapped_column(Enum(kaso_mashin.base.BinaryScale),
                                            default=kaso_mashin.base.BinaryScale.G)
    disk_format: Mapped[DiskFormat] = mapped_column(Enum(DiskFormat), default=DiskFormat.Raw)

    image_uid: Mapped[Optional[str]] = mapped_column(ForeignKey("images.uid"))
    image: Mapped[Optional['kaso_mashin.domain.image.ImageModel']] = relationship(lazy='selectin', back_populates='disks')
    instance: Mapped[Optional['kaso_mashin.domain.instance.InstanceModel']] = relationship(lazy='selectin', back_populates='disk')


class Disk(kaso_mashin.base.AggregateRoot['DiskRepository']):
    """
    Domain model entity for a disk
    """

    def __init__(
            self,
            name: str,
            path: pathlib.Path,
            size: kaso_mashin.base.BinarySizedValue =
                    kaso_mashin.base.BinarySizedValue(2, kaso_mashin.base.BinaryScale.G),
            disk_format: DiskFormat = DiskFormat.Raw,
            image: typing.Optional['kaso_mashin.domain.image.Image'] = None,
    ) -> None:
        super().__init__(name)
        self._path = path
        self._size = size
        self._disk_format = disk_format
        self._image = image
        self._instance: typing.Optional['kaso_mashin.domain.instance.Instance'] = None

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def size(self) -> kaso_mashin.base.BinarySizedValue:
        return self._size

    @size.setter
    def size(self, value: kaso_mashin.base.BinarySizedValue) -> None:
        self._size = value
        self._dirty = True

    @property
    def disk_format(self) -> DiskFormat:
        return self._disk_format

    @property
    def image(self) -> 'kaso_mashin.domain.image.Image':
        return self._image

    @property
    def instance(self) -> 'kaso_mashin.domain.instance.Instance':
        return self._instance

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._path == other.path,
            self._size == other.size,
            self._disk_format == other.disk_format,
            self._image == other.image,
        ])

    def __repr__(self) -> str:
        return (
            f"DiskEntity(uid={self.uid}, "
            f"name={self.name}, "
            f"path={self.path}, "
            f"size={self.size}, "
            f"disk_format={self.disk_format},"
            f"image={self.image})"
        )

    async def post_create(self) -> None:
        try:
            if self.path.exists():
                raise kaso_mashin.base.EntityInvariantException(status=400, msg=f'Disk at {self.path} already exists')
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.image is not None and self.size < self.image.min_disk:
                raise DiskException(status=400, msg=f"Disk size is less than image minimum size")

            class CreateDiskTask(Task):
                async def run(self,
                              path: pathlib.Path,
                              qemu_img_path: pathlib.Path,
                              size: kaso_mashin.base.BinarySizedValue,
                              disk_format: DiskFormat,
                              image: kaso_mashin.domain.Image) -> None:
                    try:
                        args = [qemu_img_path, "create", "-q", "-f", str(disk_format)]
                        if image is not None:
                            args.extend(["-F", str(disk_format), "-b", str(image.path)])
                        args.extend([str(path), str(size)])
                        subprocess.run(args, check=True)
                        await self.done('Disk created')
                    except subprocess.CalledProcessError as cpe:
                        await self.fail(f'Failed to create disk: {cpe.output}')
                    except asyncio.CancelledError:
                        self._state = TaskState.CANCELLED
                        path.unlink(missing_ok=True)

            t = self.task_service.create(CreateDiskTask(name=f'Create Disk {self.name}'),
                                         path=self.path,
                                         qemu_img_path=self.config_service.qemu_img_path,
                                         size=self.size,
                                         disk_format=self.disk_format,
                                         image=self.image)
            await t.task
            if self.image is not None:
                self.image.disks.append(self)
            await super().post_create()
        except PermissionError as pe:
            raise DiskException(status=400,
                                msg=f'No permission to create the disk at {self.path}') from pe

    async def post_modify(self) -> None:
        try:
            class ResizeTask(Task):
                async def run(self,
                              path: pathlib.Path,
                              qemu_img_path: pathlib.Path,
                              disk_format: DiskFormat,
                              current: kaso_mashin.base.BinarySizedValue,
                              new: kaso_mashin.base.BinarySizedValue):
                    try:
                        await super().run()
                        args = [qemu_img_path, "resize", "-q", "-f", str(disk_format)]
                        if current > new:
                            args.append("--shrink")
                        args += [str(path), str(new)]
                        subprocess.run(args, check=True)
                        await self.done('Successfully resized the disk')
                    except subprocess.CalledProcessError as cpe:
                        await self.fail(f'Failed to resize disk: {cpe.output}')
                    except asyncio.CancelledError:
                        self._state = TaskState.CANCELLED
                        path.unlink(missing_ok=True)

            current_size = kaso_mashin.base.BinarySizedValue(self.path.stat().st_size,
                                                               kaso_mashin.base.BinaryScale.b)
            if current_size != self._size:
                t = self.task_service.create(ResizeTask(name=f'Resize disk {self.name}'),
                                             path=self.path,
                                             qemu_img_path=self.config_service.qemu_img_path,
                                             disk_format=self.disk_format,
                                             current=current_size,
                                             new=self._size)
                await t.task
            await super().post_modify()
        except PermissionError as pe:
            raise DiskException(status=400,
                                msg=f'No permission to resize image {self.name}') from pe
        return await super().post_modify()

    async def pre_remove(self) -> None:
        try:
            # TODO: Check whether we have instances dependending on this disk
            self.path.unlink(missing_ok=True)
            if self.image is not None:
                self.image.disks.remove(self)
            return await super().pre_remove()
        except PermissionError as pe:
            raise DiskException(status=400,
                                msg=f'No permission to remove the disk at {self.path}') from pe


class DiskRepository(kaso_mashin.base.Repository[Disk, DiskModel]):
    """
    A repository of disks
    """
    entity_class = Disk
    model_class = DiskModel

    @classmethod
    async def from_model(cls, model: DiskModel, *args, **kwargs) -> Disk:
        kwargs['path'] = pathlib.Path(model.path)
        kwargs['size'] = kaso_mashin.base.BinarySizedValue(value=model.size,
                                                             scale=kaso_mashin.base.BinaryScale(model.size_scale))
        kwargs['disk_format'] = model.disk_format
        if model.image is not None:
            kwargs['image'] = await kaso_mashin.domain.Image.repository.get_by_uid(kaso_mashin.base.UniqueIdentifier(model.image.uid))
        return await super().from_model(model, *args, **kwargs)


    @classmethod
    async def to_model(cls, entity: Disk, persisted: DiskModel | None = None) -> DiskModel:
        model = await super().to_model(entity, persisted)
        model.path = str(entity.path)
        model.size = entity.size.value
        model.size_scale = entity.size.scale
        model.disk_format = entity.disk_format
        model.image_uid = None if entity.image is None else str(entity.image.uid)
        return model


class DiskCreateSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to create a disk
    """

    name: str = Field(description="Disk name", examples=["root", "data-1", "data-2"])
    # TODO: We should not have to specify the path
    path: pathlib.Path = Field(
        description="Path of the disk image on the local filesystem",
        examples=["/var/kaso/instances/root.qcow2"],
    )
    size: kaso_mashin.base.BinarySizedValue = Field(
        description="Disk size",
        examples=[kaso_mashin.base.BinarySizedValue(value=2,
                                                    scale=kaso_mashin.base.BinaryScale.G)],
    )
    disk_format: DiskFormat = Field(
        description="Disk image file format",
        examples=[DiskFormat.QCoW2, DiskFormat.Raw],
    )
    # TODO: This should be optional
    image_uid: kaso_mashin.base.UniqueIdentifier = Field(
        description="The image uid on which this disk is based on", default=None
    )


class DiskGetSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to get information about a specific disk
    """

    uid: kaso_mashin.base.UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="Disk name", examples=["root", "data-1", "data-2"])
    path: pathlib.Path = Field(
        description="Path of the disk image on the local filesystem",
        examples=["/var/kaso/instances/root.qcow2"],
    )
    size: kaso_mashin.base.BinarySizedValue = Field(
        description="Disk size",
        examples=[kaso_mashin.base.BinarySizedValue(value=2, scale=kaso_mashin.base.BinaryScale.G)],
    )
    disk_format: DiskFormat = Field(
        description="Disk image file format",
        examples=[DiskFormat.QCoW2, DiskFormat.Raw],
    )
    image_uid: kaso_mashin.base.UniqueIdentifier | None = Field(
        description="The image uid on which this disk is based on",
        optional=True,
        default=None,
    )


class DiskListSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to list disks
    """

    entries: typing.List[DiskGetSchema] = Field(description="List of disks", default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Kind")
        table.add_column("[blue]Name")
        table.add_column("[blue]CIDR")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name)
        return table


class DiskModifySchema(kaso_mashin.base.EntitySchema):
    """
    Schema to modify an existing disk
    """

    size: kaso_mashin.base.BinarySizedValue = Field(
        description="Disk size",
        examples=[kaso_mashin.base.BinarySizedValue(value=2, scale=kaso_mashin.base.BinaryScale.G)],
        optional=True,
        default=None,
    )
