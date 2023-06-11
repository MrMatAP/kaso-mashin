import typing
from sqlalchemy import String, Integer, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kaso_mashin import Base
from kaso_mashin.model import NetworkModel, ImageModel, IdentityModel

instance_to_networks = Table(
    'instance_networks',
    Base.metadata,
    Column('instance_id', ForeignKey('instances.instance_id')),
    Column('network_id', ForeignKey('networks.network_id'))
)


class InstanceModel(Base):
    """
    Represenation of an instance in the database
    """

    __tablename__ = 'instances'
    instance_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)

    path: Mapped[str] = mapped_column(String, unique=True)
    vcpu: Mapped[int] = mapped_column(Integer)
    ram: Mapped[int] = mapped_column(Integer)
    mac: Mapped[str] = mapped_column(String, nullable=True)
    image_id: Mapped[int] = mapped_column(ForeignKey('images.image_id'))
    identity_id: Mapped[int] = mapped_column(ForeignKey('identities.identity_id'))
    network_id: Mapped[int] = mapped_column(ForeignKey('networks.network_id'))
    os_disk_path: Mapped[str] = mapped_column(String)
    os_disk_size: Mapped[str] = mapped_column(String)

    network: Mapped[NetworkModel] = relationship(lazy=False)
    image: Mapped[ImageModel] = relationship(lazy=False)
    identity: Mapped[IdentityModel] = relationship(lazy=False)
