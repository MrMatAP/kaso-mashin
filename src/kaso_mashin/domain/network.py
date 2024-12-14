import enum
import ipaddress
import typing
from typing import Optional, List

import rich.box
import rich.table

from pydantic import Field
from sqlalchemy import String, Enum, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, relationship

import kaso_mashin
import kaso_mashin.base
from kaso_mashin.base import EntityNotFoundException
from kaso_mashin.services.config_service import DEFAULT_HOST_NETWORK_NAME, \
    DEFAULT_SHARED_NETWORK_NAME, DEFAULT_BRIDGED_NETWORK_NAME


class NetworkException(kaso_mashin.base.KasoMashinException):
    """
    Exception for network-related issues
    """
    pass


class NetworkKind(str, enum.Enum):
    VMNET_HOST = "vmnet-host"
    VMNET_SHARED = "vmnet-shared"
    VMNET_BRIDGED = "vmnet-bridged"


class NetworkModel(kaso_mashin.base.Model):
    """
    Representation of a network entity in the database
    """

    __tablename__ = "networks"
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[NetworkKind] = mapped_column(Enum(NetworkKind))
    cidr: Mapped[str] = mapped_column(String, unique=True)
    gateway: Mapped[str] = mapped_column(String)
    dhcp_start: Mapped[str] = mapped_column(String)
    dhcp_end: Mapped[str] = mapped_column(String)

    instances: Mapped[Optional[List['kaso_mashin.domain.instance.InstanceModel']]] = relationship(lazy='selectin', back_populates='network')


class Network(kaso_mashin.base.AggregateRoot['NetworkRepository']):
    """
    Domain model entity for a network
    """

    def __init__(
            self,
            name: str,
            kind: NetworkKind,
            cidr: ipaddress.IPv4Network,
            gateway: ipaddress.IPv4Address
    ):
        super().__init__(name)
        self._kind = kind
        self._cidr = cidr
        self._gateway = gateway
        if cidr.num_addresses < 4:
            raise kaso_mashin.base.EntityInvariantException(status=400,
                                                            msg='A network must have at least one free IP address')
        self._dhcp_start = cidr.network_address + 2
        self._dhcp_end = cidr.broadcast_address - 1
        self._instances: typing.List['kaso_mashin.domain.Instance'] = []

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

    @dhcp_start.setter
    def dhcp_start(self, value: ipaddress.IPv4Address) -> None:
        if value not in self._cidr:
            raise kaso_mashin.base.EntityInvariantException(status=400,
                                                            msg='The DHCP start address must be within the network')
        self._dhcp_start = value
        self._dirty = True

    @property
    def dhcp_end(self) -> ipaddress.IPv4Address:
        return self._dhcp_end

    @dhcp_end.setter
    def dhcp_end(self, value: ipaddress.IPv4Address) -> None:
        if value not in self._cidr:
            raise kaso_mashin.base.EntityInvariantException(status=400,
                                                            msg='The DHCP end address must be within the network')
        self._dhcp_end = value
        self._dirty = True

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self.name == other.name,
            self.kind == other.kind,
            self.cidr == other.cidr,
            self.gateway == other.gateway,
            self.dhcp_start == other.dhcp_start,
            self.dhcp_end == other.dhcp_end])

    async def post_create(self) -> None:
        duplicate = await self.repository.get_by_cidr(self._cidr)
        if duplicate is not None and duplicate.uid != self.uid:
            raise kaso_mashin.base.EntityInvariantException(status=400, msg=f'Network {duplicate.name} already uses CIDR {self.cidr}')
        return await super().post_create()

    async def pre_remove(self) -> None:
        # TODO: Check whether any instance is using this network
        return await super().pre_remove()


class NetworkRepository(kaso_mashin.base.Repository[Network, NetworkModel]):
    """
    A repository of networks
    """
    entity_class = Network
    model_class = NetworkModel

    async def get_by_cidr(self, cidr: ipaddress.IPv4Network) -> Network:
        try:
            nets = list(filter(lambda e: e.cidr == cidr, self._identity_map.values()))
            if len(nets) > 0:
                return nets[0]
            async with self._session_maker() as session:
                model = (await session.scalars(
                            select(self.model_class)
                            .where(self.model_class.cidr == str(cidr)))).one()
                return await self.from_model(model)
        except SQLAlchemyError as sae:
            raise kaso_mashin.base.KasoMashinException(status=500, msg='Failure getting a network by its cidr') from sae

    @classmethod
    async def from_model(cls, model: NetworkModel, *args, **kwargs) -> Network:
        kwargs['kind'] = model.kind
        kwargs['cidr'] = ipaddress.IPv4Network(model.cidr)
        kwargs['gateway'] = ipaddress.IPv4Address(model.gateway)
        entity = await super().from_model(model, *args, **kwargs)
        entity.dhcp_start = ipaddress.IPv4Address(model.dhcp_start)
        entity.dhcp_end = ipaddress.IPv4Address(model.dhcp_end)
        entity.dirty = False
        return entity

    @classmethod
    async def to_model(cls, entity: Network, persisted: NetworkModel | None = None) -> NetworkModel:
        model = await super().to_model(entity, persisted)
        model.kind = entity.kind
        model.cidr = str(entity.cidr)
        model.gateway = str(entity.gateway)
        model.dhcp_start = str(entity.dhcp_start)
        model.dhcp_end = str(entity.dhcp_end)
        return model

    async def initialise(self):
        await super().initialise()
        try:
            await self.get_by_name(DEFAULT_HOST_NETWORK_NAME)
        except EntityNotFoundException:
            net = Network(
                name=DEFAULT_HOST_NETWORK_NAME,
                kind=NetworkKind.VMNET_HOST,
                cidr=ipaddress.IPv4Network("10.1.0.0/24"),
                gateway=ipaddress.IPv4Address("10.1.0.1"))
            await net.save()
        try:
            await self.get_by_name(DEFAULT_SHARED_NETWORK_NAME)
        except EntityNotFoundException:
            net = Network(
                name=DEFAULT_SHARED_NETWORK_NAME,
                kind=NetworkKind.VMNET_SHARED,
                cidr=ipaddress.IPv4Network("10.2.0.0/24"),
                gateway=ipaddress.IPv4Address("10.2.0.1"))
            await net.save()
        try:
            await self.get_by_name(DEFAULT_BRIDGED_NETWORK_NAME)
        except EntityNotFoundException:
            net = Network(
                name=DEFAULT_BRIDGED_NETWORK_NAME,
                kind=NetworkKind.VMNET_BRIDGED,
                cidr=ipaddress.IPv4Network("10.3.0.0/24"),
                gateway=ipaddress.IPv4Address("10.3.0.1"))
            await net.save()

class NetworkCreateSchema(kaso_mashin.base.EntitySchema):
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

    uid: kaso_mashin.base.UniqueIdentifier = Field(
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


class NetworkListSchema(kaso_mashin.base.EntitySchema):
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
            table.add_row(str(entry.uid), str(entry.kind.value), entry.name, str(entry.cidr))
        return table


class NetworkModifySchema(kaso_mashin.base.EntitySchema):
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
