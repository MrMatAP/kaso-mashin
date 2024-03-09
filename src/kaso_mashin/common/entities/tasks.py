import typing
import enum

from pydantic import Field

from kaso_mashin import KasoMashinException
from kaso_mashin.common.base_types import (
    ORMBase, SchemaBase,
    Entity, AggregateRoot,
    UniqueIdentifier,
    EntityNotFoundException, EntityInvariantException, T_Model, T_Entity,
)


class TaskState(str, enum.Enum):
    """
    An enumeration of task state
    """
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'


class TaskException(KasoMashinException):
    pass


class TaskModel(ORMBase):
    """
    Representation of a task entity in the database.
    This is a dummy, since we do not persist tasks at this moment
    """
    __tablename__ = 'tasks'

    def merge(self, other: typing.Self):
        pass


class TaskListSchema(SchemaBase):
    """
    Schema to list tasks
    """
    uid: UniqueIdentifier = Field(description='The unique identifier', examples=['b430727e-2491-4184-bb4f-c7d6d213e093'])
    name: str = Field(description='Task name', example=['Downloading image'])
    state: TaskState = Field(description='The current state of the task', examples=[TaskState.RUNNING, TaskState.DONE])


class TaskGetSchema(TaskListSchema):
    """
    Schema to get information about a specific task
    """
    msg: str = Field(description='Task status message', examples=['Downloaded 10% of the image'])
    percent_complete: int = Field(description='Task completion', examples=[12, 100])


class TaskEntity(Entity):
    """
    Domain model entity for a task
    """

    def __init__(self,
                 owner: 'TaskAggregateRoot',
                 name: str):
        super().__init__(owner=owner)
        self._name = name
        self._state = TaskState.RUNNING
        self._msg = ''
        self._percent_complete = 0
        self._outcome: Entity | None = None

    @property
    def name(self) -> str:
        return self._name

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
    def outcome(self) -> Entity | None:
        return self._outcome

    def __eq__(self, other: 'TaskEntity') -> bool:
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._state == other.state,
            self._msg == other.msg,
            self._percent_complete == other.percent_complete,
            self._outcome == other.outcome
        ])

    def __repr__(self) -> str:
        return (
            f'<TaskEntity(uid={self.uid}, '
            f'name={self.name}, '
            f'state={self.state}, '
            f'msg={self.msg}, '
            f'percent_complete={self.percent_complete})>'
        )

    @staticmethod
    async def create(owner: 'TaskAggregateRoot', name: str) -> 'TaskEntity':
        task = TaskEntity(owner=owner, name=name)
        return await owner.create(task)

    async def progress(self, percent_complete: int, msg: str = None):
        self._percent_complete = percent_complete
        if msg is not None:
            self._msg = msg
        await self.owner.modify(self)

    async def done(self, msg: str, outcome: Entity = None):
        self._percent_complete = 100
        self._msg = msg
        self._outcome = outcome
        self._state = TaskState.DONE
        await self.owner.modify(self)

    async def fail(self, msg: str):
        self._msg = msg
        self._state = TaskState.FAILED
        await self.owner.modify(self)


class TaskAggregateRoot(AggregateRoot[TaskEntity, TaskModel]):

    async def get(self, uid: UniqueIdentifier, force_reload: bool = False) -> T_Entity:
        if uid not in self._identity_map:
            raise EntityNotFoundException(status=404, msg='No such entity')
        return self._identity_map[uid]

    async def list(self, force_reload: bool = False) -> typing.List[T_Entity]:
        return list(self._identity_map.values())

    async def create(self, entity: TaskEntity) -> TaskEntity:
        if entity.uid in self._identity_map:
            raise EntityInvariantException(status=400, msg='Entity already exists')
        if not self.validate(entity):
            raise EntityInvariantException(status=400, msg='Entity fails validation')
        self._identity_map[entity.uid] = entity
        return self._identity_map[entity.uid]

    # Only methods in the entity should call this
    async def modify(self, entity: TaskEntity):
        if entity.uid not in self._identity_map:
            raise EntityNotFoundException(status=400, msg='Entity was not created by this aggregate root')
        if not self.validate(entity):
            raise EntityInvariantException(status=400, msg='Entity fails validation')
        self._identity_map[entity.uid] = entity

    async def remove(self, uid: UniqueIdentifier):
        if uid not in self._identity_map:
            raise EntityNotFoundException(status=400, msg='Entity was not created by this aggregate root')
        del self._identity_map[uid]

    def validate(self, entity: TaskEntity) -> bool:
        return all([
            entity is not None,
            isinstance(entity.uid, UniqueIdentifier)
        ])

    # We do not currently persist tasks
    async def _to_model(self, entity: TaskEntity) -> T_Model:
        pass

    # We do not currently persist tasks
    async def _from_model(self, model: T_Model) -> T_Entity:
        pass
