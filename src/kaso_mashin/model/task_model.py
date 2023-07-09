import enum
import uuid
import pydantic


class TaskState(enum.Enum):
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'


class TaskSchema(pydantic.BaseModel):
    """
    A generic task model
    """
    task_id: uuid.UUID
    name: str
    state: TaskState = TaskState.RUNNING
    msg: str = ''
    percent_complete: int = 0

    def progress(self, percent_complete: int, msg: str):
        self.percent_complete = percent_complete
        self.msg = msg

    def success(self, msg: str):
        self.percent_complete = 100
        self.state = TaskState.DONE
        self.msg = msg

    def fail(self, msg: str):
        self.state = TaskState.FAILED
        self.msg = msg
