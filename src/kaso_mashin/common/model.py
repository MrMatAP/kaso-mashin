from typing import Optional, List

from sqlalchemy import String, Enum, UnicodeText, Integer, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Model, BinaryScale
from .types import IdentityKind, DiskFormat, NetworkKind, BootstrapKind


class IdentityModel(Model):
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


class ImageModel(Model):
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

    disks: Mapped[Optional[List['DiskModel']]] = relationship(lazy='selectin', back_populates='image')


class DiskModel(Model):
    """
    Representation of a disk entity in the database
    """

    __tablename__ = "disks"
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer, default=0)
    size_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    disk_format: Mapped[DiskFormat] = mapped_column(Enum(DiskFormat), default=DiskFormat.Raw)

    image_uid: Mapped[Optional[str]] = mapped_column(ForeignKey("images.uid"))
    image: Mapped[Optional[ImageModel]] = relationship(lazy='selectin', back_populates='disks')


class NetworkModel(Model):
    """
    Representation of a network entity in the database
    """

    __tablename__ = "networks"
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[NetworkKind] = mapped_column(Enum(NetworkKind))
    cidr: Mapped[str] = mapped_column(String, unique=True)
    gateway: Mapped[str] = mapped_column(String)
    dhcp_start: Mapped[str] = mapped_column(String)
    dhcp_end: Mapped[str] = mapped_column(String)


class BootstrapModel(Model):
    """
    Representation of a bootstrap entity in the database
    """

    __tablename__ = "bootstraps"
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[BootstrapKind] = mapped_column(Enum(BootstrapKind))
    content: Mapped[str] = mapped_column(UnicodeText)


class InstanceModel(Model):
    """
    Representation of an instance entity in the database
    """

    __tablename__ = "instances"
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String())
    uefi_code: Mapped[str] = mapped_column(String())
    uefi_vars: Mapped[str] = mapped_column(String())
    vcpu: Mapped[int] = mapped_column(Integer, default=0)
    ram: Mapped[int] = mapped_column(Integer, default=2)
    ram_scale: Mapped[str] = mapped_column(Enum(BinaryScale), default=BinaryScale.G)
    mac: Mapped[str] = mapped_column(String)
    network_uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), "sqlite"))
    image_uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), "sqlite"))
    os_disk_uid: Mapped[str] = mapped_column(UUID(as_uuid=True).with_variant(String(32), "sqlite"))
    bootstrap_uid: Mapped[str] = mapped_column(
        UUID(as_uuid=True).with_variant(String(32), "sqlite")
    )
    bootstrap_file: Mapped[str] = mapped_column(String)
