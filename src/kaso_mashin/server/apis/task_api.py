from starlette.websockets import WebSocket, WebSocketDisconnect

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
        self._router.add_api_websocket_route(path='/notify',
                                             endpoint=self.notify)

    async def notify(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(dict(foo="bar"))
                task = await self._runtime.queue_service.tasks()
                await websocket.send_json(TaskGetSchema.model_validate(task))
        except WebSocketDisconnect as wd:
            # TODO: Log the disconnection
            pass
        except Exception as e:
            pass

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.task_repository
