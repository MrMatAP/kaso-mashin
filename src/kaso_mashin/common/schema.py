import ipaddress
import pathlib
import typing

import pydantic
import rich.box
import rich.table
from pydantic import BaseModel, ConfigDict, Field

from kaso_mashin.common import UniqueIdentifier, BinarySizedValue, BinaryScale, IdentityKind, \
    DiskFormat, NetworkKind, BootstrapKind, InstanceState, TaskRelation, TaskState
from kaso_mashin.common.exceptions import KasoMashinException
from kaso_mashin.common.types import DEFAULT_MIN_VCPU, DEFAULT_MIN_RAM, DEFAULT_MIN_DISK


class EntitySchema(BaseModel):
    """
    Schema base class for serialised entities
    """

    model_config = ConfigDict(from_attributes=True)

T_EntitySchema = typing.TypeVar("T_EntitySchema", bound=EntitySchema)
T_EntityModifySchema = typing.TypeVar("T_EntityModifySchema", bound=EntitySchema)
T_EntityGetSchema = typing.TypeVar("T_EntityGetSchema", bound=EntitySchema)
T_EntityListSchema = typing.TypeVar("T_EntityListSchema", bound=EntitySchema)
T_EntityListEntrySchema = typing.TypeVar("T_EntityListEntrySchema", bound=EntitySchema)
T_EntityCreateSchema = typing.TypeVar("T_EntityCreateSchema", bound=EntitySchema)

class GetSchema(EntitySchema):
    pass


class ModifySchema(EntitySchema):
    pass


class ExceptionSchema(pydantic.BaseModel):
    """
    Schema for an exception
    """

    kind: str = pydantic.Field(description="Kind of exception")
    status: int = pydantic.Field(description="The exception status code", default=500)
    msg: str = pydantic.Field(description="A user-readable error description")

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": 400, "msg": "I did not like your input, at all"}]
        }
    }


class BootstrapGetSchema(EntitySchema):
    """
    Schema to get a bootstrap
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="The bootstrap name", examples=["k8s-master"])
    kind: BootstrapKind = Field(description="The bootstrap kind", examples=[BootstrapKind.IGNITION])
    content: str = Field(description="The bootstrap content template")
    required_keys: typing.List[str] = Field(
        description="Required keys to render this bootstrap template"
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Kind", self.kind)
        table.add_row("[blue]Required Keys", ",".join(self.required_keys))
        table.add_row("[blue]Content", self.content)
        return table


class BootstrapListSchema(EntitySchema):
    """
    Schema to list bootstraps
    """

    entries: typing.List[BootstrapGetSchema] = Field(
        description="List of bootstraps", default_factory=list
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Kind")
        table.add_column("[blue]Name")
        for entry in self.entries:
            table.add_row(str(entry.uid), str(entry.kind.value), entry.name)
        return table


class BootstrapCreateSchema(EntitySchema):
    """
    Schema to create a bootstrap
    """

    name: str = Field(description="The bootstrap name", examples=["k8s-master"])
    kind: BootstrapKind = Field(description="The bootstrap kind", examples=[BootstrapKind.IGNITION])
    content: str = Field(description="The bootstrap content template")


class BootstrapModifySchema(EntitySchema):
    """
    Schema to modify a bootstrap
    """

    name: str = Field(description="The bootstrap name", examples=["k8s-master"])
    kind: BootstrapKind = Field(description="The bootstrap kind", examples=[BootstrapKind.IGNITION])
    content: str = Field(description="The bootstrap content template")


class DiskCreateSchema(EntitySchema):
    """
    Schema to create a disk
    """

    name: str = Field(description="Disk name", examples=["root", "data-1", "data-2"])
    # TODO: We should not have to specify the path
    path: pathlib.Path = Field(
        description="Path of the disk image on the local filesystem",
        examples=["/var/kaso/instances/root.qcow2"],
    )
    size: BinarySizedValue = Field(
        description="Disk size",
        examples=[BinarySizedValue(value=2, scale=BinaryScale.G)],
    )
    disk_format: DiskFormat = Field(
        description="Disk image file format",
        examples=[DiskFormat.QCoW2, DiskFormat.Raw],
    )
    # TODO: This should be optional
    image_uid: UniqueIdentifier = Field(
        description="The image uid on which this disk is based on", default=None
    )


class DiskGetSchema(EntitySchema):
    """
    Schema to get information about a specific disk
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="Disk name", examples=["root", "data-1", "data-2"])
    path: pathlib.Path = Field(
        description="Path of the disk image on the local filesystem",
        examples=["/var/kaso/instances/root.qcow2"],
    )
    size: BinarySizedValue = Field(
        description="Disk size",
        examples=[BinarySizedValue(value=2, scale=BinaryScale.G)],
    )
    disk_format: DiskFormat = Field(
        description="Disk image file format",
        examples=[DiskFormat.QCoW2, DiskFormat.Raw],
    )
    image_uid: UniqueIdentifier | None = Field(
        description="The image uid on which this disk is based on",
        optional=True,
        default=None,
    )


class DiskListSchema(EntitySchema):
    """
    Schema to list disks
    """

    entries: typing.List[DiskGetSchema] = Field(description="List of disks", default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Kind")
        table.add_column("[blue]Name")
        table.add_column("[blue]CIDR")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name)
        return table


class DiskModifySchema(EntitySchema):
    """
    Schema to modify an existing disk
    """

    size: BinarySizedValue = Field(
        description="Disk size",
        examples=[BinarySizedValue(value=2, scale=BinaryScale.G)],
        optional=True,
        default=None,
    )


class IdentityCreateSchema(EntitySchema):
    """
    Schema to create an identity
    """

    name: str = Field(description="The identity name", examples=["imfeldma"])
    kind: IdentityKind = Field(description="The identity kind")
    gecos: str = Field(description="The identity GECOS")
    homedir: pathlib.Path = Field(description="The home directory")
    shell: str = Field(description="The identity shell")
    credential: str = Field(description="The identity credential")


class IdentityGetSchema(EntitySchema):
    """
    Schema to get identities
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="The identity name", examples=["imfeldma"])
    kind: IdentityKind = Field(description="The identity kind")
    gecos: str = Field(description="The identity GECOS")
    homedir: pathlib.Path = Field(description="The home directory")
    shell: str = Field(description="The identity shell")
    credential: str = Field(description="The identity credential")

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Kind", self.kind)
        table.add_row("[blue]GECOS", self.gecos or "")
        table.add_row("[blue]Home Directory", str(self.homedir) or "")
        table.add_row("[blue]Shell", self.shell or "")
        table.add_row("[blue]Credential", self.credential or "")
        return table


class IdentityListSchema(EntitySchema):
    """
    Schema to list identities
    """

    entries: typing.List[IdentityGetSchema] = Field(
        description="List of identities", default_factory=list
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Kind")
        table.add_column("[blue]Name")
        table.add_column("[blue]Gecos")
        for entry in self.entries:
            table.add_row(str(entry.uid), str(entry.kind.value), entry.name, entry.gecos)
        return table


class IdentityModifySchema(EntitySchema):
    """
    Schema to modify an identity
    """

    name: str = Field(
        description="The identity name",
        examples=["imfeldma"],
        optional=True,
        default=None,
    )
    kind: IdentityKind = Field(description="The identity kind", optional=True, default=None)
    gecos: str = Field(description="The identity GECOS", optional=True, default=None)
    homedir: pathlib.Path = Field(description="The home directory", optional=True, default=None)
    shell: str = Field(description="The identity shell", optional=True, default=None)
    credential: str = Field(description="The identity credential", optional=True, default=None)


class ImageCreateSchema(EntitySchema):
    """
    Schema to create an image
    """

    name: str = Field(description="The image name", examples=["ubuntu", "flatpack", "debian"])
    url: str = Field(
        description="URL from which the image is sourced",
        examples=[
            "https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img"
        ],
    )
    min_vcpu: int = Field(
        description="Optional minimum number of CPU vcores to run this image",
        default=DEFAULT_MIN_VCPU,
        examples=[DEFAULT_MIN_VCPU, 2, 4],
    )
    min_ram: BinarySizedValue = Field(
        description="Optional minimum RAM size to run this image",
        default=DEFAULT_MIN_RAM,
        examples=[DEFAULT_MIN_RAM, BinarySizedValue(value=2, scale=BinaryScale.G)],
    )
    min_disk: BinarySizedValue = Field(
        description="Optional minimum disk size to run this image",
        default=DEFAULT_MIN_DISK,
        examples=[DEFAULT_MIN_DISK, BinarySizedValue(value=10, scale=BinaryScale.G)],
    )


class ImageGetSchema(ImageCreateSchema):
    """
    Schema to get information about a specific image
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    path: pathlib.Path = Field(description="Path to the image on the local disk")

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Path", str(self.path))
        table.add_row("[blue]Min VCPU", str(self.min_vcpu))
        table.add_row("[blue]Min RAM", f"{self.min_ram.value} {self.min_ram.scale}")
        table.add_row("[blue]Min Disk", f"{self.min_disk.value} {self.min_disk.scale}")
        return table


class ImageListSchema(EntitySchema):
    """
    Schema to list images
    """

    entries: typing.List[ImageGetSchema] = Field(description="List of images", default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Name")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name)
        return table


class ImageModifySchema(EntitySchema):
    """
    Schema to modify an existing image
    """

    name: typing.Optional[str] = Field(
        description="The image name", examples=["ubuntu", "flatpack", "debian"]
    )
    min_vcpu: typing.Optional[int] = Field(
        description="Optional minimum number of CPU vcores to run this image",
        default=DEFAULT_MIN_VCPU,
        examples=[DEFAULT_MIN_VCPU, 2, 4],
    )
    min_ram: typing.Optional[BinarySizedValue] = Field(
        description="Optional minimum RAM size to run this image",
        default=DEFAULT_MIN_RAM,
        examples=[DEFAULT_MIN_RAM, BinarySizedValue(2, BinaryScale.G)],
    )
    min_disk: typing.Optional[BinarySizedValue] = Field(
        description="Optional minimum disk size to run this image",
        default=DEFAULT_MIN_DISK,
        examples=[DEFAULT_MIN_DISK, BinarySizedValue(10, BinaryScale.G)],
    )


class InstanceCreateSchema(EntitySchema):
    """
    Schema to create an instance
    """

    name: str = Field(description="The instance name", examples=["k8s-master", "your-mom"])
    vcpu: int = Field(description="Number of virtual CPU cores", examples=[2])
    ram: BinarySizedValue = Field(
        description="Amount of RAM",
        examples=[BinarySizedValue(value=2, scale=BinaryScale.G)],
    )
    os_disk_size: BinarySizedValue = Field(description="Size of the OS disk")
    image_uid: str = Field(
        description="The image UID from which to create the OS disk from",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    network_uid: str = Field(
        description="The network on which to run this instance",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    bootstrap_uid: str = Field(
        description="The bootstrap uid",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )


class InstanceGetSchema(EntitySchema):
    """
    Schema to get information about a specific instance
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier of the instance",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="The instance name", examples=["k8s-master", "your-mom"])
    path: pathlib.Path = Field(description="Path of the instance on the local disk")
    vcpu: int = Field(description="Number of virtual CPU cores", examples=[2])
    ram: BinarySizedValue = Field(
        description="Amount of RAM",
        examples=[BinarySizedValue(value=2, scale=BinaryScale.G)],
    )
    mac: str = Field(description="Instance MAC address")
    network_uid: UniqueIdentifier = Field(
        description="The network UID on which to run this instance"
    )
    image_uid: UniqueIdentifier = Field(description="The image UID")
    os_disk_uid: UniqueIdentifier = Field(description="The OS disk UID")
    os_disk_size: BinarySizedValue = Field(description="Size of the OS disk")
    bootstrap_uid: UniqueIdentifier = Field(description="The bootstrapper uid")
    bootstrap_file: pathlib.Path = Field(
        description="The path to the bootstrap file on the local disk"
    )
    state: InstanceState = Field(
        description="The instance state",
        examples=[InstanceState.STOPPED, InstanceState.STARTED],
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row("[blue]Path", str(self.path))
        table.add_row("[blue]VCPUs", str(self.vcpu))
        table.add_row("[blue]RAM", f"{self.ram.value} {self.ram.scale}")
        table.add_row("[blue]MAC", self.mac)
        table.add_row("[blue]Network UID", str(self.network_uid))
        table.add_row("[blue]Image UID", str(self.image_uid))
        table.add_row("[blue]OS Disk UID", str(self.os_disk_uid))
        table.add_row("[blue]Bootstrap UID", str(self.bootstrap_uid))
        table.add_row("[blue]Bootstrap File", str(self.bootstrap_file))
        table.add_row("[blue]State", str(self.state))
        return table


class InstanceListSchema(EntitySchema):
    """
    Schema to list instances
    """

    entries: typing.List[InstanceGetSchema] = Field(
        description="List of instances", default_factory=list
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Name")
        table.add_column("[blue]State")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name, str(entry.state))
        return table


class InstanceModifySchema(EntitySchema):
    """
    Schema to modify an existing instance
    """

    state: typing.Optional[InstanceState] = Field(description="The state of the instance")


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
            table.add_row(str(entry.uid), str(entry.kind.value), entry.name, str(entry.cidr))
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


class TaskGetSchema(EntitySchema):
    """
    Schema to get information about a specific task
    """

    uid: UniqueIdentifier = Field(
        description="The unique identifier",
        examples=["b430727e-2491-4184-bb4f-c7d6d213e093"],
    )
    name: str = Field(description="Task name", examples=["Downloading image"])
    relation: TaskRelation = Field(description="Entity the task relates to",
                                   examples=[TaskRelation.BOOTSTRAPS, TaskRelation.DISKS],
                                   default=TaskRelation.GENERAL)
    state: TaskState = Field(
        description="The current state of the task",
        examples=[TaskState.RUNNING, TaskState.DONE],
    )
    msg: str = Field(description="Task status message", examples=["Downloaded 10% of the image"])
    percent_complete: int = Field(description="Task completion", examples=[12, 100])
    outcome: UniqueIdentifier | None = Field(
        description="The resulting uid of the task if applicable"
    )

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("[blue]UID", str(self.uid))
        table.add_row("[blue]Name", self.name)
        table.add_row('[blue]Relation', str(self.relation))
        table.add_row("[blue]State", str(self.state))
        table.add_row("[blue]Message", str(self.msg))
        table.add_row("[blue]Percent Complete", f"{self.percent_complete} %")
        return table


class TaskListSchema(EntitySchema):
    """
    Schema to list tasks
    """

    entries: typing.List[TaskGetSchema] = Field(description="List of tasks", default_factory=list)

    def __rich__(self):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column("[blue]UID")
        table.add_column("[blue]Name")
        table.add_column('[blue]Relation')
        table.add_column("[blue]State")
        for entry in self.entries:
            table.add_row(str(entry.uid), entry.name, str(entry.relation), str(entry.state))
        return table


class TaskException(KasoMashinException):
    pass
