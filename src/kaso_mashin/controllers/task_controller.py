import typing
import uuid


from kaso_mashin import KasoMashinException
from kaso_mashin.config import Config
from kaso_mashin.controllers import AbstractController
from kaso_mashin.db import DB
from kaso_mashin.model import TaskSchema


class TaskController(AbstractController):
    """
    A task controller
    """

    def __init__(self, config: Config, db: DB):
        super().__init__(config, db)
        self._tasks: typing.Dict[uuid.UUID, TaskSchema] = {}

    def list(self) -> typing.List[TaskSchema]:
        return self._tasks.values()

    def get(self, task_id: uuid.UUID) -> TaskSchema:
        if task_id not in self._tasks:
            raise KasoMashinException(status=400, msg='No such task')
        return self._tasks[task_id]

    def create(self, name: str) -> TaskSchema:
        model = TaskSchema(task_id=uuid.uuid4(), name=name)
        self._tasks[model.task_id] = model
        return model