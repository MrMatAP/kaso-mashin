import typing
import uuid
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import TaskSchema


class TaskAPI(AbstractAPI):
    """
    The Task API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(tags=['tasks'])
        self._router.add_api_route('/', self.list_tasks, methods=['GET'],
                                   response_model=typing.List[TaskSchema])
        self._router.add_api_route('/{task_id}', self.get_task, methods=['GET'],
                                   response_model=TaskSchema)

    async def list_tasks(self):
        """
        List current tasks
        Returns:
            A list of tasks
        """
        return self.task_controller.list()

    async def get_task(self, task_id: uuid.UUID):
        """
        Get a specific task
        Args:
            task_id: The task id

        Returns:
            A specific task
        """
        return self.task_controller.get(task_id)
