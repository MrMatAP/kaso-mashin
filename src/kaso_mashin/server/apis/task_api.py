import typing
import uuid
import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import ExceptionSchema, TaskSchema


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
        self._router.add_api_route('/', self.list_tasks, methods=['GET'],
                                   summary='List tasks',
                                   description='The returned list includes all tasks. These can be distinguished by '
                                               'their state field on whether they are currently running, have failed '
                                               'or have completed successfully.',
                                   response_description='A list of tasks',
                                   status_code=200,
                                   response_model=typing.List[TaskSchema])
        self._router.add_api_route('/{task_id}', self.get_task, methods=['GET'],
                                   summary='Get a task',
                                   description='Get a specific task by its unique UUID.',
                                   response_description='A task',
                                   status_code=200,
                                   response_model=TaskSchema)

    async def list_tasks(self):
        return self.task_controller.list()

    async def get_task(self,
                       task_id: typing.Annotated[uuid.UUID,
                                                 fastapi.Path(title='Task UUID',
                                                              description='A unique task UUID',
                                                              examples=['79563383-56f8-4d0e-a419-1b8fe5804219'])]):
        return self.task_controller.get(task_id)
