import asyncio

from kaso_mashin.common.base_types import Service
from kaso_mashin.common.entities import TaskEntity


class MessagingService(Service):

    def __init__(self, runtime: "Runtime"):
        super().__init__(runtime)
        self._task_queue = asyncio.Queue(maxsize=0)
        self._event_queue = asyncio.Queue(maxsize=0)
        self._logger.info("Started messaging service")

    async def queue_event(self, event):
        self._event_queue.put_nowait(event)

    async def events(self):
        return await self._event_queue.get()

    async def queue_task(self, task: TaskEntity):
        await self._task_queue.put(task)
        self._logger.info(f"Queue is now {self._task_queue.qsize()}")

    async def tasks(self) -> TaskEntity:
        return await self._task_queue.get()
