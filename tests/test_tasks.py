import pytest

import asyncio

from conftest import task_service
from kaso_mashin.common.services import Task, TaskService
from kaso_mashin.common import TaskState


class ReporterTask(Task):
    async def run(self, task_service: TaskService):
        await super().run()
        tasks = list(filter(lambda t: not isinstance(t, self.__class__), await task_service.list()))
        while all([t.state == TaskState.RUNNING for t in tasks]):
            for task in tasks:
                self._logger.info(repr(task))
            await asyncio.sleep(1)
        await self.done()


class ProgressTask(Task):
    async def run(self):
        try:
            await super().run()
            current = 1
            while current <= 5:
                await self.progress(current / 5 * 100)
                await asyncio.sleep(1)
                current += 1
            await self.done()
        except asyncio.CancelledError:
            self._logger.info(f'Task {self._uid} cancelling: {self._msg}')
            self._state = TaskState.CANCELLED
        finally:
            self._logger.info(f'Task {self._uid} finalising: {self._msg}')


class CancellerTask(Task):
    async def run(self, task_to_cancel: Task):
        await super().run()
        await asyncio.sleep(2)
        await task_to_cancel.cancel()
        await self.done(f'Successfully cancelled task {task_to_cancel.uid}')


@pytest.mark.asyncio
async def test_task_service(task_service: TaskService):
    tasks = list()
    for i in range(1, 3):
        tasks.append(task_service.create(ProgressTask(name=f'Progress {i}')))
    tasks.append(task_service.create(CancellerTask(name=f'Canceller 1'), task_to_cancel=tasks[0]))
    tasks.append(task_service.create(ReporterTask(name='Reporter'), task_service=task_service))
    await asyncio.gather(*[t.task for t in tasks])
    assert len(tasks) == len(task_service.list())
    assert tasks[0].state == TaskState.CANCELLED
    assert tasks[0].percent_complete < 100
    assert tasks[1].state == TaskState.DONE
    assert tasks[2].state == TaskState.DONE

    done_tasks = task_service.get_by_state(state=TaskState.DONE)
    assert len(done_tasks) == 2
    assert tasks[1] in done_tasks
    assert tasks[2] in done_tasks

    cancelled_tasks = task_service.get_by_state(state=TaskState.CANCELLED)
    assert len(cancelled_tasks) == 1
    assert tasks[0] in cancelled_tasks
