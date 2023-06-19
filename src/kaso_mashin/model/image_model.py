from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import Base

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


class ImageModel(Base):
    """
    Representation of an image in the database
    """

    __tablename__ = 'images'
    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    path: Mapped[str] = mapped_column(String, unique=True)
