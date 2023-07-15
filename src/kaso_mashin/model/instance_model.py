from sqlalchemy import String, Integer, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import pydantic

from kaso_mashin import Base
from kaso_mashin.model import DbPath, SchemaPath, NetworkModel, ImageModel, IdentityModel

instance_to_networks = Table(
    'instance_networks',
    Base.metadata,
    Column('instance_id', ForeignKey('instances.instance_id')),
    Column('network_id', ForeignKey('networks.network_id'))
)


class InstanceBaseSchema(pydantic.BaseModel):
    """
    The common base schema for an instance. It deliberately does not contain generated fields such as the instance_id
    because we do not allow that to be provided during creation of an instance
    """
    name: str = pydantic.Field(description='The instance name')
    vcpu: int = pydantic.Field(description='Number of virtual CPUs')
    ram: int = pydantic.Field(description='Amount of RAM in MB')
    bootstrapper: str = pydantic.Field(description='Name of the bootstrapper')
    image_id: int = pydantic.Field('Image ID to use as the backing OS disk')
    network_id: int = pydantic.Field('Network ID to connect the instance to')

    model_config = pydantic.ConfigDict(from_attributes=True)


class InstanceSchema(InstanceBaseSchema):
    """
    The full schema of an instance, extends the base schema with fields generated when the instance is created
    """
    instance_id: int = pydantic.Field(description='The unique instance ID')
    path: SchemaPath = pydantic.Field(description='Path to the instance on the local disk')
    mac: str = pydantic.Field(description='The generated MAC address')


class InstanceCreateSchema(InstanceBaseSchema):
    """
    An input schema to create an instance
    """
    pass



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
