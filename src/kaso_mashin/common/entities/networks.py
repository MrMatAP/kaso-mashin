import enum
import ipaddress

from pydantic import Field

from sqlalchemy import String, Enum, select
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntitySchema,
    EntityModel,
    Entity,
    AggregateRoot,
    AsyncRepository
)

DEFAULT_HOST_NETWORK_NAME = 'default_host_network'
DEFAULT_BRIDGED_NETWORK_NAME = 'default_bridged_network'
DEFAULT_SHARED_NETWORK_NAME = 'default_shared_network'


class NetworkKind(str, enum.Enum):
    VMNET_HOST = 'host'
    VMNET_SHARED = 'shared'
    VMNET_BRIDGED = 'bridged'


class NetworkListSchema(EntitySchema):
    """
    Schema to list networks
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='The network name', examples=['foo', 'bar', 'baz'])
    kind: NetworkKind = Field(description='Network kind',
                              examples=[NetworkKind.VMNET_SHARED, NetworkKind.VMNET_HOST])
    cidr: str = Field(description='The network CIDR',
                      examples=['10.0.0.0/16', '172.16.2.0/24'])


class NetworkCreateSchema(EntitySchema):
    """
    Schema to create a network
    """
    name: str = Field(description='The network name', examples=['foo', 'bar', 'baz'])
    kind: NetworkKind = Field(description='Network kind',
                              examples=[NetworkKind.VMNET_SHARED, NetworkKind.VMNET_HOST])
    cidr: str = Field(description='The network CIDR',
                      examples=['10.0.0.0/16', '172.16.2.0/24'])
    gateway: str = Field(description='The network gateway',
                         examples=['10.0.0.1', '172.16.2.1'])


class NetworkGetSchema(NetworkCreateSchema):
    """
    Schema to get information about a specific network
    """
    uid: UniqueIdentifier = Field(description='The unique identifier',
                                  examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])


class NetworkModifySchema(EntitySchema):
    """
    Schema to modify networks
    """
    name: str = Field(description='The network name',
                      examples=['foo', 'bar', 'baz'],
                      optional=True,
                      default=None)
    cidr: str = Field(description='The network CIDR',
                      examples=['10.0.0.0/16', '172.16.2.0/24'],
                      optional=True,
                      default=None)
    gateway: str = Field(description='The network gateway',
                         examples=['10.0.0.1', '172.16.2.1'],
                         optional=True,
                         default=None)


class NetworkException(KasoMashinException):
    """
    Exception for network-related issues
    """
    pass


class NetworkModel(EntityModel):
    """
    Representation of a network entity in the database
    """
    __tablename__ = 'networks'
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[NetworkKind] = mapped_column(Enum(NetworkKind))
    cidr: Mapped[str] = mapped_column(String)
    gateway: Mapped[str] = mapped_column(String)


class NetworkEntity(Entity, AggregateRoot):
    """
    Domain model entity for a network
    """

    def __init__(self,
                 name: str,
                 kind: NetworkKind,
                 cidr: str,
                 gateway: str):
        super().__init__()
        self._name = name
        self._kind = kind
        self._cidr = cidr
        self._gateway = gateway
        self._network = ipaddress.IPv4Network(cidr)

    @property
    def name(self) -> str:
        return self._name

    @property
    def kind(self) -> NetworkKind:
        return self._kind

    @property
    def cidr(self) -> str:
        return self._cidr

    @property
    def gateway(self) -> str:
        return self._gateway

    @property
    def network(self) -> ipaddress.IPv4Address:
        return self._network.network_address

    @property
    def netmask(self) -> ipaddress.IPv4Address:
        return self._network.netmask

    def __eq__(self, other: 'NetworkEntity') -> bool:
        return all([
            super().__eq__(other),
            self.name == other.name,
            self.kind == other.kind,
            self.cidr == other.cidr,
            self.gateway == other.gateway
        ])

    def __repr__(self) -> str:
        return (
            f'<NetworkEntity(uid={self.uid}, '
            f'name={self.name},'
            f'kind={self.kind},'
            f'cidr={self.cidr},'
            f'gateway={self.gateway})>'
        )

    @staticmethod
    async def from_model(model: NetworkModel) -> 'NetworkEntity':
        network = NetworkEntity(name=model.name,
                                kind=NetworkKind(model.kind),
                                cidr=model.cidr,
                                gateway=model.gateway)
        network._uid = UniqueIdentifier(model.uid)
        return network

    async def to_model(self, model: NetworkModel | None = None) -> NetworkModel:
        if model is None:
            return NetworkModel(uid=str(self.uid),
                                name=self.name,
                                kind=self.kind,
                                cidr=self.cidr,
                                gateway=self.gateway)
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.kind = self.kind
            model.cidr = self.cidr
            model.gateway = self.gateway
            return model

    @staticmethod
    async def create(name: str,
                     kind: NetworkKind,
                     cidr: str,
                     gateway: str) -> 'NetworkEntity':
        network = NetworkEntity(name=name,
                                kind=kind,
                                cidr=cidr,
                                gateway=gateway)
        await NetworkEntity.repository.create(network)
        return network

    async def modify(self, schema: NetworkModifySchema) -> 'NetworkEntity':
        if schema.name is not None:
            self._name = schema.name
        if schema.cidr is not None:
            self._cidr = schema.cidr
        if schema.gateway is not None:
            self._gateway = schema.gateway
        return await self.repository.modify(self)

    async def remove(self):
        await NetworkEntity.repository.remove(self.uid)


class NetworkRepository(AsyncRepository[NetworkEntity, NetworkModel]):

    async def get_by_name(self, name: str) -> NetworkEntity | None:
        async with self._session_maker() as session:
            model = await session.scalar(select(self._model_class)
                                         .where(self._model_class.name == name))
            if model is None:
                return None
            return await self._aggregate_root_class.from_model(model)
