import enum

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
