import enum

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column
import pydantic

from kaso_mashin import Base
from kaso_mashin.common.custom_types import IP4Address, SchemaIPv4


class NetworkKind(str, enum.Enum):
    VMNET_HOST = 'host'
    VMNET_SHARED = 'shared'
    VMNET_BRIDGED = 'bridged'


class NetworkBaseSchema(pydantic.BaseModel):
    """
    The common base schema for a network. It deliberately does not contain generated fields we do not
    allow to be provided when creating an network
    """
    model_config = pydantic.ConfigDict(from_attributes=True)

    name: str = pydantic.Field(description='The network name',
                               examples=['mrmat-shared'])
    kind: NetworkKind = pydantic.Field(description='The network kind',
                                       default=NetworkKind.VMNET_SHARED,
                                       examples=['shared'])


class NetworkCreateSchema(NetworkBaseSchema):
    """
    Input schema for creating a network
    """
    ns4: SchemaIPv4 | None = pydantic.Field(description='The IPv4 nameserver',
                                     default=None,
                                     examples=['172.16.4.15'])
    dhcp4_start: SchemaIPv4 | None = pydantic.Field(description='The IPv4 DHCP4 start address',
                                             default=None,
                                             examples=['172.16.4.100'])
    dhcp4_end: SchemaIPv4 | None = pydantic.Field(description='The IPV4 DHCP4 end address',
                                           default=None,
                                           examples=['172.16.4.254'])
    host_phone_home_port: str | None = pydantic.Field(description='The port on which we listen for instances to phone '
                                                                  'home',
                                                      default=None,
                                                      examples=['172.16.4.183'])


class NetworkModifySchema(pydantic.BaseModel):
    """
    Input schema for modifying a network
    """
    ns4: SchemaIPv4 | None = pydantic.Field(description='The IPv4 nameserver',
                                     default=None,
                                     examples=['172.16.4.15'])
    dhcp4_start: SchemaIPv4 | None = pydantic.Field(description='The IPv4 DHCP4 start address',
                                             default=None,
                                             examples=['172.16.4.100'])
    dhcp4_end: SchemaIPv4 | None = pydantic.Field(description='The IPV4 DHCP4 end address',
                                           default=None,
                                           examples=['172.16.4.254'])
    host_phone_home_port: str | None = pydantic.Field(description='The port on which we listen for instances to phone '
                                                                  'home',
                                                      default=None,
                                                      examples=['172.16.4.183'])


class NetworkModel(Base):
    """
    Representation of a network in the database
    """
    __tablename__ = 'networks'
    network_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    kind: Mapped[NetworkKind] = mapped_column(Enum(NetworkKind))

    host_if: Mapped[str] = mapped_column(String, nullable=True)
    host_ip4: Mapped[str] = mapped_column(IP4Address, nullable=True)
    nm4: Mapped[str] = mapped_column(IP4Address, nullable=True)
    gw4: Mapped[str] = mapped_column(IP4Address, nullable=True)
    ns4: Mapped[str] = mapped_column(IP4Address, nullable=True)
    dhcp4_start: Mapped[str] = mapped_column(IP4Address, nullable=True)
    dhcp4_end: Mapped[str] = mapped_column(IP4Address, nullable=True)
    host_phone_home_port: Mapped[int] = mapped_column(Integer)

    @staticmethod
    def from_schema(schema: NetworkCreateSchema | NetworkModifySchema) -> 'NetworkModel':
        model = NetworkModel(
            ns4=schema.ns4,
            dhcp4_start=schema.dhcp4_start,
            dhcp4_end=schema.dhcp4_end,
            host_phone_home_port=schema.host_phone_home_port)
        if isinstance(schema, NetworkCreateSchema):
            model.name = schema.name
            model.kind = schema.kind
        return model

    def __eq__(self, other) -> bool:
        return all([
            isinstance(other, NetworkModel),
            self.network_id == other.network_id,
            self.name == other.name,
            self.kind == other.kind,
            self.host_if == other.host_if,
            self.host_ip4 == other.host_ip4,
            self.nm4 == other.nm4,
            self.gw4 == other.gw4,
            self.ns4 == other.ns4,
            self.dhcp4_start == other.dhcp4_start,
            self.dhcp4_end == other.dhcp4_end
        ])

    def __repr__(self) -> str:
        return f'NetworkModel(id={self.network_id!r}, ' \
               f'name={self.name!r}, ' \
               f'kind={self.kind!r}, ' \
               f'host_ip4={self.host_ip4!r}, ' \
               f'host_phone_home_port{self.host_phone_home_port!r}, ' \
               f'nm4={self.nm4}, ' \
               f'gw4={self.gw4!r}, ' \
               f'ns4={self.nm4!r}' \
               f'dhcp4_start={self.dhcp4_start!r}, ' \
               f'dhcp4_end={self.dhcp4_end!r}, ' \
               f')'
