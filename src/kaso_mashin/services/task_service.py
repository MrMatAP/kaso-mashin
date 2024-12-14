import asyncio
import enum
import logging
import typing
import uuid

import rich.box
import rich.table
from pydantic import Field

import kaso_mashin.base


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


class Task:
    """
    Domain model entity for a task
    """

    def __init__(self,
                 name: str,
                 relation: TaskRelation = TaskRelation.GENERAL,
                 msg: str = "Task created"):
        self._uid = uuid.uuid4()
        self._name = name
        self._relation = relation
        self._state = TaskState.INITIALIZED
        self._msg = msg
        self._percent_complete = 0
        self._task: asyncio.Task | None = None
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    def uid(self) -> kaso_mashin.base.UniqueIdentifier:
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    @property
    def relation(self) -> TaskRelation:
        return self._relation

    @property
    def state(self) -> TaskState:
        return self._state

    @state.setter
    def state(self, value: TaskState):
        self._state = value

    @property
    def msg(self) -> str:
        return self._msg

    @property
    def percent_complete(self) -> int:
        return self._percent_complete

    @property
    def task(self) -> asyncio.Task:
        return self._task

    @task.setter
    def task(self, value: asyncio.Task) -> None:
        self._task = value

    async def run(self, *args, **kwargs):
        self._state = 'Task running'
        self._state = TaskState.RUNNING
        self._logger.info(f'Task {self._uid} running: {self._msg}')

    async def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._msg = 'Task cancelled'
            self._state = TaskState.CANCELLED
            self._logger.info(f'Task {self._uid} cancelled: {self._msg}')

    def __eq__(self, other: typing.Any) -> bool:
        return all(
            [
                super().__eq__(other),
                self._uid == other.uid,
                self._name == other.name,
                self._relation == other.relation,
                self._state == other.state,
                self._msg == other.msg,
                self._percent_complete == other.percent_complete,
            ]
        )

    def __lt__(self, other: typing.Any) -> bool:
        return self.uid < other.uid

    async def progress(self, percent_complete: int, msg: str | None = None) -> None:
        self._percent_complete = percent_complete
        if msg is not None:
            self._msg = msg

    async def done(self, msg: str = 'Task done'):
        self._percent_complete = 100
        self._msg = msg
        self._state = TaskState.DONE
        self._logger.debug(f'Task {self._uid} done')

    async def fail(self, msg: str = 'Task failed'):
        self._msg = msg
        self._state = TaskState.FAILED
        self._logger.debug(f'Task {self._uid} failed: {self._msg}')

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(uid={self.uid}, "
            f"name={self.name}, "
            f'relation={self.relation}, '
            f"state={self.state}, "
            f"msg={self.msg}, "
            f"percent_complete={self.percent_complete}"
            f")")


class TaskService:
    """
    A repository of tasks
    """

    def __init__(self):
        Task.repository = self
        self._identity_map: typing.Dict[kaso_mashin.base.UniqueIdentifier, Task] = {}

    def get_by_uid(self, uid: kaso_mashin.base.UniqueIdentifier) -> Task:
        if uid not in self._identity_map:
            raise kaso_mashin.base.EntityNotFoundException()
        return self._identity_map[uid]

    def get_by_state(self, state: TaskState) -> typing.List[Task]:
        return list(filter(lambda x: x.state == state, self._identity_map.values()))

    def list(self) -> typing.List[Task]:
        return list(self._identity_map.values())

    def create(self, entity: Task, callback: typing.Callable | None = None,  *args, **kwargs) -> Task:
        if entity.uid in self._identity_map:
            raise kaso_mashin.base.EntityInvariantException(status=400, msg="Task already exists")
        self._identity_map[entity.uid] = entity
        entity.task = asyncio.create_task(entity.run(*args, **kwargs))
        if callback is not None:
            entity.task.add_done_callback(callback)
        return self._identity_map[entity.uid]

    def remove(self, uid: kaso_mashin.base.UniqueIdentifier):
        if uid not in self._identity_map:
            raise kaso_mashin.base.EntityNotFoundException()
        del self._identity_map[uid]


class TaskGetSchema(kaso_mashin.base.EntitySchema):
    """
    Schema to get information about a specific task
    """

    uid: kaso_mashin.base.UniqueIdentifier = Field(
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
    outcome: kaso_mashin.base.UniqueIdentifier | None = Field(
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


class TaskListSchema(kaso_mashin.base.EntitySchema):
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


class TaskException(kaso_mashin.base.KasoMashinException):
    pass
