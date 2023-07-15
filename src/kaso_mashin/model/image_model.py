from sqlalchemy import String
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
    The common base schema for an image. It deliberately does not contain generated fields we do not
    allow to be provided when creating an image
    """
    name: str = pydantic.Field(description='The image name')
    path: SchemaPath = pydantic.Field(description='Path to the image on the local disk')

    model_config = pydantic.ConfigDict(from_attributes=True)


class ImageSchema(ImageBaseSchema):
    """
    The full schema of an image, extends the ImageBaseSchema with the image_id because that is
    only available after the image is created
    """
    image_id: int = pydantic.Field(description='The image id')

    model_config = {
        'json_schema_extra': {
            'examples': [{
                'image_id': 1,
                'name': 'ubuntu-jammy',
                'path': '/Users/dude/var/kaso/images/ubuntu-jammy.qcow2'
            }]
        }
    }


class ImageCreateSchema(pydantic.BaseModel):
    """
    An input schema to create an image
    """
    name: str
    url: str

    model_config = {
        'json_schema_extra': {
            'examples': [{
                'image_id': 1,
                'name': 'ubuntu-jammy',
                'path': '/Users/dude/var/kaso/images/ubuntu-jammy.qcow2'
            }]
        }
    }


class ImageModel(Base):
    """
    Representation of an image in the database
    """

    __tablename__ = 'images'
    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    path: Mapped[str] = mapped_column(DbPath, unique=True)
