import typing
import uuid

import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import ExceptionSchema
from kaso_mashin.common.entities import (
    TaskListSchema, TaskGetSchema
)


class TaskAPI(AbstractAPI):
    """
    The Task API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(tags=['tasks'],
                                         responses={
                                             404: {'model': ExceptionSchema, 'description': 'Task not found'},
                                             400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route(path='/',
                                   endpoint=self.list_tasks,
                                   methods=['GET'],
                                   summary='List tasks',
                                   description='List all currently known tasks',
                                   response_description='A list of tasks',
                                   status_code=200,
                                   response_model=typing.List[TaskListSchema])
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.get_task,
                                   methods=['GET'],
                                   summary='Get a task',
                                   description='Get information about a task specified by its unique ID',
                                   response_description='A task',
                                   status_code=200,
                                   response_model=TaskGetSchema)

    async def list_tasks(self):
        entities = await self._runtime.task_repository.list(force_reload=True)
        return [TaskListSchema.model_validate(e) for e in entities]

    async def get_task(self,
                       uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Task UUID',
                                                                     description='A unique task UUID',
                                                                     examples=[
                                                                         '79563383-56f8-4d0e-a419-1b8fe5804219'])]):
        entity = await self._runtime.task_repository.get_by_uid(uid)
        return TaskGetSchema.model_validate(entity)
