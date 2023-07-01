from sqlalchemy import String, Integer, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kaso_mashin import Base
from kaso_mashin.model import DbPath, NetworkModel, ImageModel, IdentityModel

instance_to_networks = Table(
    'instance_networks',
    Base.metadata,
    Column('instance_id', ForeignKey('instances.instance_id')),
    Column('network_id', ForeignKey('networks.network_id'))
)


class InstanceModel(Base):
    """
    Representation of an instance in the database
    """

    __tablename__ = 'instances'
    instance_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)

    path: Mapped[str] = mapped_column(DbPath, unique=True)
    vcpu: Mapped[int] = mapped_column(Integer)
    ram: Mapped[int] = mapped_column(Integer)
    mac: Mapped[str] = mapped_column(String, nullable=True)
    static_ip4: Mapped[str] = mapped_column(String, nullable=True)
    bootstrapper: Mapped[str] = mapped_column(String)
    image_id: Mapped[int] = mapped_column(ForeignKey('images.image_id'))
    identity_id: Mapped[int] = mapped_column(ForeignKey('identities.identity_id'))
    network_id: Mapped[int] = mapped_column(ForeignKey('networks.network_id'))
    os_disk_path: Mapped[str] = mapped_column(DbPath)
    os_disk_size: Mapped[str] = mapped_column(DbPath)
    ci_disk_path: Mapped[str] = mapped_column(DbPath, nullable=True)

    network: Mapped[NetworkModel] = relationship(lazy=False)
    image: Mapped[ImageModel] = relationship(lazy=False)
    identity: Mapped[IdentityModel] = relationship(lazy=False)
