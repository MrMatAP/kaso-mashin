from aievents import Events

from kaso_mashin.common.base_types import Service


# To subscribe:
#         self.runtime.event_service.on_task_fail += <local async method>
# To emit:
#         await self.runtime.event_service.on_task_fail(self)


class EventService(Service, Events):
    __events__ = ("on_task_create", "on_task_progress", "on_task_done", "on_task_fail")

    def __init__(self, runtime: "Runtime"):
        super().__init__(runtime=runtime)
        self._logger.info("Started messaging service")
