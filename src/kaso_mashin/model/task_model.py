import enum
import uuid
import pydantic


class TaskState(enum.Enum):
    """
    An enumeration of task state
    """
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'


class TaskSchema(pydantic.BaseModel):
    """
    Schema for a task being processed
    """
    task_id: uuid.UUID = pydantic.Field(description='Unique identifier of this task')
    name: str = pydantic.Field(description='A short description')
    state: TaskState = pydantic.Field(description='The current state', default=TaskState.RUNNING)
    msg: str = pydantic.Field(description='A short message', default='')
    percent_complete: int = pydantic.Field(description='Current percentage of task completion', default=0)

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'task_id': '79563383-56f8-4d0e-a419-1b8fe5804219',
                    'name': 'Downloading image ubuntu-jammy',
                    'state': 'running',
                    'msg': '',
                    'percent_complete': 50
                }
            ]
        }
    }

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
