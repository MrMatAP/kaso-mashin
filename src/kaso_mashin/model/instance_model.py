import typing
from sqlalchemy import String, Integer, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import pydantic

from kaso_mashin import Base
from kaso_mashin.custom_types import DbPath, SchemaPath
from kaso_mashin.model import NetworkModel, ImageModel, IdentityModel

instance_to_networks = Table(
    'instance_networks',
    Base.metadata,
    Column('instance_id', ForeignKey('instances.instance_id')),
    Column('network_id', ForeignKey('networks.network_id'))
)

instance_to_identities = Table(
    'instance_identities',
    Base.metadata,
    Column('instance_id', ForeignKey('instances.instance_id')),
    Column('identity_id', ForeignKey('identities.identity_id'))
)


class InstanceSchema(pydantic.BaseModel):
    """
    The full schema of an instance, extends the base schema with fields generated when the instance is created
    """
    model_config = pydantic.ConfigDict(from_attributes=True)

    instance_id: int = pydantic.Field(description='The unique instance ID', examples=[1])
    name: str = pydantic.Field(description='The instance name', examples=['mrmat-jammy'])

    path: SchemaPath = pydantic.Field(description='Path to the instance on the local disk',
                                      examples=['/Users/mrmat/var/kaso/instances/mrmat-jammy'])
    mac: str = pydantic.Field(description='The generated MAC address', examples=['08:00:20:0a:0b:0c'])
    vcpu: int = pydantic.Field(description='Number of virtual CPUs', examples=[2])
    ram: int = pydantic.Field(description='Amount of RAM in MB', examples=[2048])
    bootstrapper: str = pydantic.Field(description='Name of the bootstrapper')
    image_id: int = pydantic.Field(description='Image ID to use as the backing OS disk', examples=[1])
    network_id: int = pydantic.Field(description='Network ID to connect the instance to', examples=[1])
    os_disk_path: SchemaPath = pydantic.Field(description='OS disk path', examples=['/path/to/os.qcow'])
    os_disk_size: str = pydantic.Field(description='OS disk size', examples=['5G'])
    ci_base_path: SchemaPath = pydantic.Field(description='CI base path', examples=['/path/to/cloud-init'])
    ci_disk_path: SchemaPath = pydantic.Field(description='CI disk path', examples=['/path/to/ci.img'])
    vm_script_path: SchemaPath = pydantic.Field(description='VM script path', examples=['/path/to/vm.sh'])


class InstanceCreateSchema(pydantic.BaseModel):
    """
    An input schema to create an instance
    """
    name: str = pydantic.Field(description='The instance name', examples=['mrmat-jammy'])
    vcpu: int = pydantic.Field(description='Number of virtual CPUs', examples=[2])
    ram: int = pydantic.Field(description='Amount of RAM in MB', examples=[2048])
    bootstrapper: str = pydantic.Field(description='Name of the bootstrapper')
    image_id: int = pydantic.Field(description='Image ID to use as the backing OS disk', examples=[1])
    network_id: int = pydantic.Field(description='Network ID to connect the instance to', examples=[1])
    os_disk_size: str = pydantic.Field(description='The OS disk size in GB', default='5G', examples=['5G'])
    identities: list = pydantic.Field(description='The identities on that instance', default_factory=list, examples=['1'])


class InstanceModifySchema(pydantic.BaseModel):
    """
    An input schema to modify an instance
    """
    vcpu: int = pydantic.Field(description='Number of virtual CPUs', examples=[2])
    ram: int = pydantic.Field(description='Amount of RAM in MB', examples=[2048])


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
    network_id: Mapped[int] = mapped_column(ForeignKey('networks.network_id'))
    os_disk_path: Mapped[str] = mapped_column(DbPath)
    os_disk_size: Mapped[str] = mapped_column(String)
    ci_base_path: Mapped[str] = mapped_column(DbPath, nullable=True)
    ci_disk_path: Mapped[str] = mapped_column(DbPath, nullable=True)
    vm_script_path: Mapped[str] = mapped_column(DbPath, nullable=True)

    network: Mapped[NetworkModel] = relationship(lazy=False)
    image: Mapped[ImageModel] = relationship(lazy=False)
    identities: Mapped[typing.List[IdentityModel]] = relationship(secondary=instance_to_identities)

    @staticmethod
    def from_schema(schema: InstanceCreateSchema | InstanceModifySchema) -> 'InstanceModel':
        model = InstanceModel(
            vcpu=schema.vcpu,
            ram=schema.ram)
        if isinstance(schema, InstanceCreateSchema):
            model.name = schema.name
            model.bootstrapper = schema.bootstrapper
            model.image_id = schema.image_id
            model.network_id = schema.network_id
            model.os_disk_size = schema.os_disk_size
            model.identities = [IdentityModel(identity_id=i) for i in schema.identities]
        return model

    def __eq__(self, other) -> bool:
        return all([
            isinstance(other, InstanceModel),
            self.instance_id == other.instance_id,
            self.name == other.name,
            self.path == other.path,
            self.vcpu == other.vcpu,
            self.ram == other.ram,
            self.mac == other.mac,
            self.static_ip4 == other.static_ip4,
            self.bootstrapper == other.bootstrapper,
            self.image_id == other.image_id,
            self.network_id == other.network_id,
            self.os_disk_path == other.os_disk_path,
            self.os_disk_size == other.os_disk_size,
            self.ci_base_path == other.ci_base_path,
            self.ci_disk_path == other.ci_disk_path,
            self.vm_script_path == other.vm_script_path])

    def __repr__(self) -> str:
        return f'InstanceModel(instance_id={self.instance_id}, name="{self.name}", path="{self.path}")'
