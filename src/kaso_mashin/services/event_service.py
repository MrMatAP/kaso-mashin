from aievents import Events


class EventService(Events):
    """
    To subscribe:
    self.runtime.event_service.on_task_fail += <local async method>
    To emit:
    await self.runtime.event_service.on_task_fail(self)
    """
    __events__ = ("on_task_create", "on_task_progress", "on_task_done", "on_task_fail")

    def __init__(self):
        super().__init__()
        self._logger.info("Started messaging service")
