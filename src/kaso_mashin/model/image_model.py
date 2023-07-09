from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
import pydantic

from kaso_mashin import Base
from kaso_mashin.model import DbPath, SchemaPath

ImageURLs = {
    'ubuntu-bionic': 'https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img',
    'ubuntu-focal': 'https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-arm64.img',
    'ubuntu-jammy': 'https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img',
    'ubuntu-kinetic': 'https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-arm64.img',
    'ubuntu-lunar': 'https://cloud-images.ubuntu.com/lunar/current/lunar-server-cloudimg-arm64.img',
    'ubuntu-mantic': 'https://cloud-images.ubuntu.com/mantic/current/mantic-server-cloudimg-arm64.img',
    'freebsd-14': 'https://download.freebsd.org/ftp/snapshots/VM-IMAGES/14.0-CURRENT/amd64/Latest/'
                  'FreeBSD-14.0-CURRENT-amd64.qcow2.xz'
}


class ImageBaseSchema(pydantic.BaseModel):
    """
    The common base schema for an image. It deliberately does not contain image_id because we do
    not allow that to be provided during creation of an image
    """
    name: str
    path: SchemaPath
    downloaded: int

    class Config:
        from_attributes = True


class ImageSchema(ImageBaseSchema):
    """
    The full schema of an image, extends the ImageBaseSchema with the image_id because that is
    only available after the image is created
    """
    image_id: int


class ImageCreateSchema(pydantic.BaseModel):
    """
    An input schema to create an image
    """
    name: str
    url: str


class ImageModel(Base):
    """
    Representation of an image in the database
    """

    __tablename__ = 'images'
    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    path: Mapped[str] = mapped_column(DbPath, unique=True)
    downloaded: Mapped[int] = mapped_column(Integer, default=0)
