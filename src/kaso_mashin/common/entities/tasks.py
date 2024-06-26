import typing
import enum

from pydantic import Field
import rich.table
import rich.box
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from kaso_mashin import KasoMashinException
from kaso_mashin.common import (
    UniqueIdentifier,
    EntityNotFoundException,
    EntityInvariantException,
    EntitySchema,
    EntityModel,
    T_EntityModel,
    Entity,
    AggregateRoot,
    T_AggregateRoot,
    AsyncRepository,
)


class TaskState(str, enum.Enum):
    """
    An enumeration of task state
    """

    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


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


class TaskModel(EntityModel):
    """
    Representation of a task entity in the database.
    This is a dummy, since we do not persist tasks
    """

    __tablename__ = "tasks"


class TaskEntity(Entity, AggregateRoot):
    """
    Domain model entity for a task
    """

    def __init__(self,
                 name: str,
                 relation: TaskRelation = TaskRelation.GENERAL,
                 msg: str = "Task created"):
        super().__init__()
        self._name = name
        self._relation = relation
        self._state = TaskState.RUNNING
        self._msg = msg
        self._percent_complete = 0
        self._outcome: UniqueIdentifier | None = None

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
    def outcome(self) -> UniqueIdentifier | None:
        return self._outcome

    @staticmethod
    async def from_model(model: TaskModel) -> "TaskEntity":
        raise NotImplementedError

    async def to_model(self, model: TaskModel | None = None) -> TaskModel:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        return all(
            [
                super().__eq__(other),
                self._name == other.name,
                self._relation == other.relation,
                self._state == other.state,
                self._msg == other.msg,
                self._percent_complete == other.percent_complete,
                self._outcome == other.outcome,
            ]
        )

    def __repr__(self) -> str:
        return (
            f"TaskEntity(uid={self.uid}, "
            f"name={self.name}, "
            f'relation={self.relation}, '
            f"state={self.state}, "
            f"msg={self.msg}, "
            f"percent_complete={self.percent_complete}),"
            f"outcome={self.outcome})"
        )

    @staticmethod
    async def create(name: str,
                     relation: TaskRelation = TaskRelation.GENERAL,
                     msg: str = "Task created") -> "TaskEntity":
        task = TaskEntity(name=name, relation=relation, msg=msg)
        return await TaskEntity.repository.create(task)

    async def progress(self, percent_complete: int, msg: str | None = None) -> None:
        self._percent_complete = percent_complete
        if msg is not None:
            self._msg = msg
        await self.repository.modify(self)

    async def done(self, msg: str, outcome: UniqueIdentifier | None = None):
        self._percent_complete = 100
        self._msg = msg
        self._outcome = outcome
        self._state = TaskState.DONE
        await self.repository.modify(self)
        self._logger.debug(f'Task {self._uid} done')

    async def fail(self, msg: str):
        self._msg = msg
        self._state = TaskState.FAILED
        await self.repository.modify(self)
        self._logger.debug(f'Task {self._uid} failed: {self._msg}')


class TaskRepository(AsyncRepository[TaskEntity, TaskModel]):

    def __init__(
        self,
        runtime: "Runtime",
        session_maker: async_sessionmaker[AsyncSession],
        aggregate_root_class: typing.Type[T_AggregateRoot],
        model_class: typing.Type[T_EntityModel],
    ):
        super().__init__(
            runtime=runtime,
            session_maker=session_maker,
            aggregate_root_class=aggregate_root_class,
            model_class=model_class,
        )
        self._identity_map: typing.Dict[UniqueIdentifier, TaskEntity] = {}

    async def get_by_uid(self, uid: UniqueIdentifier) -> TaskEntity:
        if uid not in self._identity_map:
            raise EntityNotFoundException(status=404, msg="No such entity")
        return self._identity_map[uid]

    async def list(self, force_reload: bool = False) -> typing.List[TaskEntity]:
        return list(self._identity_map.values())

    async def create(self, entity: TaskEntity) -> TaskEntity:
        if entity.uid in self._identity_map:
            raise EntityInvariantException(status=400, msg="Entity already exists")
        self._identity_map[entity.uid] = entity
        return self._identity_map[entity.uid]

    async def modify(self, entity: TaskEntity) -> TaskEntity:
        if entity.uid not in self._identity_map:
            raise EntityNotFoundException(status=400, msg="No such entity")
        self._identity_map[entity.uid] = entity
        return entity

    async def remove(self, uid: UniqueIdentifier):
        if uid not in self._identity_map:
            raise EntityNotFoundException(status=400, msg="No such entity")
        del self._identity_map[uid]