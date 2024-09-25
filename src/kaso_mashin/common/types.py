import enum

from .base import BinarySizedValue, BinaryScale

DEFAULT_K8S_MASTER_TEMPLATE_NAME = "default_k8s_master"
DEFAULT_K8S_SLAVE_TEMPLATE_NAME = "default_k8s_slave"
DEFAULT_MIN_VCPU = 0
DEFAULT_MIN_RAM = BinarySizedValue(0, BinaryScale.G)
DEFAULT_MIN_DISK = BinarySizedValue(0, BinaryScale.G)
DEFAULT_MAC_PREFIX = "00:50:56"
DEFAULT_HOST_NETWORK_NAME = "default_host_network"
DEFAULT_BRIDGED_NETWORK_NAME = "default_bridged_network"
DEFAULT_SHARED_NETWORK_NAME = "default_shared_network"


class IdentityKind(enum.StrEnum):
    PUBKEY = "pubkey"
    PASSWORD = "password"


class NetworkKind(str, enum.Enum):
    VMNET_HOST = "vmnet-host"
    VMNET_SHARED = "vmnet-shared"
    VMNET_BRIDGED = "vmnet-bridged"


class BootstrapKind(str, enum.Enum):
    IGNITION = "ignition"
    CLOUD_INIT = "cloud-init"


class DiskFormat(enum.StrEnum):
    Raw = "raw"
    QCoW2 = "qcow2"
    VDI = "vdi"


class InstanceState(str, enum.Enum):
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    STARTED = "STARTED"


class TaskRelation(str, enum.Enum):
    """
    An enumeration of what the task relates to
    """
    BOOTSTRAPS = "bootstraps"
    DISKS = "disks"
    IDENTITIES = "identities"
    IMAGES = "images"
    INSTANCES = "instances"
    NETWORKS = "networks"
    GENERAL = "general"


class TaskState(str, enum.Enum):
    """
    An enumeration of task state
    """
    INITIALIZED = "initialized"
    CREATED = "created"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
