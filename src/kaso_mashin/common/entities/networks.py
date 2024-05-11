import typing
import enum
import ipaddress

from pydantic import Field
from sqlalchemy import String, Enum, select
from sqlalchemy.orm import Mapped, mapped_column

import rich.table
import rich.box

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntitySchema,
    EntityModel,
    Entity,
    AggregateRoot,
    AsyncRepository,
)

DEFAULT_HOST_NETWORK_NAME = "default_host_network"
DEFAULT_BRIDGED_NETWORK_NAME = "default_bridged_network"
DEFAULT_SHARED_NETWORK_NAME = "default_shared_network"


class NetworkKind(str, enum.Enum):
    VMNET_HOST = "vmnet-host"
    VMNET_SHARED = "vmnet-shared"
    VMNET_BRIDGED = "vmnet-bridged"


class NetworkException(KasoMashinException):
    """
    Exception for network-related issues
    """

    pass


class NetworkCreateSchema(EntitySchema):
    """
    Schema to create a network
    """

    name: str = Field(description="The network name", examples=["foo", "bar", "baz"])
    kind: NetworkKind = Field(
        description="Network kind",
        examples=[NetworkKind.VMNET_SHARED, NetworkKind.VMNET_HOST],
    )
    cidr: ipaddress.IPv4Network = Field(
        description="The network CIDR", examples=["10.0.0.0/16", "172.16.2.0/24"]
    )
    gateway: ipaddress.IPv4Address = Field(
        description="The network gateway", examples=["10.0.0.1", "172.16.2.1"]
    )
    dhcp_start: typing.Optional[ipaddress.IPv4Address] = Field(
        description="The dhcp start IPv4 address",
        examples=["172.16.2.10"],
        optional=True,
        default=None,
    )
    dhcp_end: typing.Optional[ipaddress.IPv4Address] = Field(
        description="The dhcp end IPv4 address",
        examples=["172.16.2.254"],
        optional=True,
        default=None,
    )


class NetworkGetSchema(NetworkCreateSchema):
    """
    Schema to get information about a specific network
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Kind", self.kind)
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]CIDR", str(self.cidr))
        table.add_row("[blue]Gateway", str(self.gateway))
        table.add_row("[blue]DHCP Range", f"{self.dhcp_start} - {self.dhcp_end}")
        return table


class NetworkListSchema(EntitySchema):
    """
    Schema to list networks
    """

    entries: typing.List[NetworkGetSchema] = Field(
        description="List of networks", default_factory=list
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Kind")
        table.add_column("[blue]Name")
        table.add_column("[blue]CIDR")
        for entry in self.entries:
            table.add_row(
                str(entry.uid), str(entry.kind.value), entry.name, str(entry.cidr)
            )
        return table


class NetworkModifySchema(EntitySchema):
    """
    Schema to modify networks
    """

    name: typing.Optional[str] = Field(
        description="The network name",
        examples=["foo", "bar", "baz"],
        optional=True,
        default=None,
    )
    cidr: typing.Optional[ipaddress.IPv4Network] = Field(
        description="The network CIDR",
        examples=["10.0.0.0/16", "172.16.2.0/24"],
        optional=True,
        default=None,
    )
    gateway: typing.Optional[ipaddress.IPv4Address] = Field(
        description="The network gateway",
        examples=["10.0.0.1", "172.16.2.1"],
        optional=True,
        default=None,
    )
    dhcp_start: typing.Optional[ipaddress.IPv4Address] = Field(
        description="The dhcp start IPv4 address",
        examples=["172.16.2.10"],
        optional=True,
        default=None,
    )
    dhcp_end: typing.Optional[ipaddress.IPv4Address] = Field(
        description="The dhcp end IPv4 address",
        examples=["172.16.2.254"],
        optional=True,
        default=None,
    )


class NetworkModel(EntityModel):
    """
    Representation of a network entity in the database
    """

    __tablename__ = "networks"
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[NetworkKind] = mapped_column(Enum(NetworkKind))
    cidr: Mapped[str] = mapped_column(String)
    gateway: Mapped[str] = mapped_column(String)
    dhcp_start: Mapped[str] = mapped_column(String)
    dhcp_end: Mapped[str] = mapped_column(String)


class NetworkEntity(Entity, AggregateRoot):
    """
    Domain model entity for a network
    """

    def __init__(
        self,
        name: str,
        kind: NetworkKind,
        cidr: ipaddress.IPv4Network,
        gateway: ipaddress.IPv4Address,
        dhcp_start: ipaddress.IPv4Address,
        dhcp_end: ipaddress.IPv4Address,
    ):
        super().__init__()
        self._name = name
        self._kind = kind
        self._cidr = cidr
        self._gateway = gateway
        self._dhcp_start = dhcp_start
        self._dhcp_end = dhcp_end

    @property
    def name(self) -> str:
        return self._name

    @property
    def kind(self) -> NetworkKind:
        return self._kind

    @property
    def cidr(self) -> ipaddress.IPv4Network:
        return self._cidr

    @property
    def netmask(self) -> ipaddress.IPv4Address:
        return self._cidr.netmask

    @property
    def gateway(self) -> ipaddress.IPv4Address:
        return self._gateway

    @property
    def dhcp_start(self) -> ipaddress.IPv4Address:
        return self._dhcp_start

    @property
    def dhcp_end(self) -> ipaddress.IPv4Address:
        return self._dhcp_end

    def __eq__(self, other: "NetworkEntity") -> bool:
        return all(
            [
                super().__eq__(other),
                self.name == other.name,
                self.kind == other.kind,
                self.cidr == other.cidr,
                self.gateway == other.gateway,
                self.dhcp_start == other.dhcp_start,
                self.dhcp_end == other.dhcp_end,
            ]
        )

    def __repr__(self) -> str:
        return (
            f"NetworkEntity(uid={self.uid}, "
            f"name={self.name},"
            f"kind={self.kind},"
            f"cidr={self.cidr},"
            f"gateway={self.gateway},"
            f"dhcp_start={self.dhcp_start},"
            f"dhcp_end={self.dhcp_end}"
            ")"
        )

    @staticmethod
    async def from_model(model: NetworkModel) -> "NetworkEntity":
        network = NetworkEntity(
            name=model.name,
            kind=NetworkKind(model.kind),
            cidr=ipaddress.IPv4Network(model.cidr),
            gateway=ipaddress.IPv4Address(model.gateway),
            dhcp_start=ipaddress.IPv4Address(model.dhcp_start),
            dhcp_end=ipaddress.IPv4Address(model.dhcp_end),
        )
        network._uid = UniqueIdentifier(model.uid)
        return network

    async def to_model(self, model: NetworkModel | None = None) -> NetworkModel:
        if model is None:
            return NetworkModel(
                uid=str(self.uid),
                name=self.name,
                kind=self.kind,
                cidr=str(self.cidr),
                gateway=str(self.gateway),
                dhcp_start=str(self.dhcp_start),
                dhcp_end=str(self.dhcp_end),
            )
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.kind = self.kind
            model.cidr = str(self.cidr)
            model.gateway = str(self.gateway)
            model.dhcp_start = str(self.dhcp_start)
            model.dhcp_end = str(self.dhcp_end)
            return model

    @staticmethod
    async def create(
        name: str,
        kind: NetworkKind,
        cidr: ipaddress.IPv4Network,
        gateway: ipaddress.IPv4Address,
        dhcp_start: ipaddress.IPv4Address = None,
        dhcp_end: ipaddress.IPv4Address = None,
    ) -> "NetworkEntity":
        if dhcp_start is None or dhcp_end is None:
            network = ipaddress.IPv4Network(cidr)
            hosts = list(network.hosts())
            dhcp_start = hosts[2] or dhcp_start
            dhcp_end = hosts[-1] or dhcp_end
        network = NetworkEntity(
            name=name,
            kind=kind,
            cidr=cidr,
            gateway=gateway,
            dhcp_start=dhcp_start,
            dhcp_end=dhcp_end,
        )
        await NetworkEntity.repository.create(network)
        return network

    async def modify(self, schema: NetworkModifySchema) -> "NetworkEntity":
        if schema.name is not None:
            self._name = schema.name
        if schema.cidr is not None:
            self._cidr = schema.cidr
        if schema.gateway is not None:
            self._gateway = schema.gateway
        if schema.dhcp_start is not None:
            self._dhcp_start = schema.dhcp_start
        if schema.dhcp_end is not None:
            self._dhcp_end = schema.dhcp_end
        return await self.repository.modify(self)

    async def remove(self):
        await NetworkEntity.repository.remove(self.uid)


class NetworkRepository(AsyncRepository[NetworkEntity, NetworkModel]):

    async def get_by_name(self, name: str) -> NetworkEntity | None:
        async with self._session_maker() as session:
            model = await session.scalar(
                select(self._model_class).where(self._model_class.name == name)
            )
            if model is None:
                return None
            return await self._aggregate_root_class.from_model(model)
