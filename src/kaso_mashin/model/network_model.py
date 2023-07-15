import enum

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column
import pydantic

from kaso_mashin import Base
from kaso_mashin.model import IP4Address


class NetworkKind(enum.Enum):
    VMNET_HOST = 'host'
    VMNET_SHARED = 'shared'
    VMNET_BRIDGED = 'bridged'


class NetworkBaseSchema(pydantic.BaseModel):
    """
    The common base schema for a network. It deliberately does not contain generated fields we do not
    allow to be provided when creating an network
    """
    name: str = pydantic.Field(description='The network name')
    kind: NetworkKind = pydantic.Field(description='The network kind', default=NetworkKind.VMNET_SHARED)

    class Config:
        from_attributes = True


class NetworkSchema(NetworkBaseSchema):
    """
    A network
    """
    network_id: int = pydantic.Field(description='The unique network id')
    host_if: str = pydantic.Field(description='The name of the host interface this network is currently attached to')
    host_ip4: str = pydantic.Field(description='The IPv4 address of the host')
    nm4: str = pydantic.Field(description='The IPv4 netmask')
    gw4: str = pydantic.Field(description='The IPv4 gateway')
    ns4: str = pydantic.Field(description='The IPv4 nameserver')
    dhcp4_start: str = pydantic.Field(description='The IPv4 DHCP4 start address')
    dhcp4_end: str = pydantic.Field(description='The IPV4 DHCP4 end address')


class NetworkCreateSchema(NetworkBaseSchema):
    """
    Input schema for creating a network
    """
    pass


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
    host_phone_home_port: Mapped[int] = mapped_column(Integer)
    nm4: Mapped[str] = mapped_column(IP4Address, nullable=True)
    gw4: Mapped[str] = mapped_column(IP4Address, nullable=True)
    ns4: Mapped[str] = mapped_column(IP4Address, nullable=True)
    dhcp_start: Mapped[str] = mapped_column(IP4Address, nullable=True)
    dhcp_end: Mapped[str] = mapped_column(IP4Address, nullable=True)

    def __repr__(self) -> str:
        return f'NetworkModel(id={self.network_id!r}, ' \
               f'name={self.name!r}, ' \
               f'kind={self.kind!r}, ' \
               f'host_ip4={self.host_ip4!r}, ' \
               f'host_phone_home_port{self.host_phone_home_port!r}, ' \
               f'nm4={self.nm4}, ' \
               f'gw4={self.gw4!r}, ' \
               f'ns4={self.nm4!r}' \
               f'dhcp_start={self.dhcp_start!r}, ' \
               f'dhcp_end={self.dhcp_end!r}, ' \
               f')'
