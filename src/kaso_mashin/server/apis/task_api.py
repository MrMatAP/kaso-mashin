from kaso_mashin.common import AsyncRepository
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.entities import (
    TaskListSchema,
    TaskGetSchema,
)


class TaskAPI(
    BaseAPI[
        TaskListSchema, TaskGetSchema, TaskGetSchema, TaskGetSchema
    ]
):
    """
    The Task API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(
            runtime=runtime,
            name="Task",
            list_schema_type=TaskListSchema,
            get_schema_type=TaskGetSchema,
            create_schema_type=TaskGetSchema,
            modify_schema_type=TaskGetSchema,
        )
        self._router.routes = list(
            filter(lambda route: route.name in ["get", "list"], self._router.routes)
        )

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.task_repository
