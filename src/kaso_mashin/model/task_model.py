import enum
import uuid
import pydantic


class TaskState(str, enum.Enum):
    """
    An enumeration of task state
    """
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'


class TaskSchema(pydantic.BaseModel):
    """
    A Task
    """
    task_id: uuid.UUID = pydantic.Field(description='The unique task identifier',
                                        examples=['79563383-56f8-4d0e-a419-1b8fe5804219'])
    name: str = pydantic.Field(description='A short description',
                               examples=['Downloading image ubuntu-jammy'])
    state: TaskState = pydantic.Field(description='The current task state',
                                      default=TaskState.RUNNING,
                                      examples=['running'])
    msg: str = pydantic.Field(description='A short message',
                              default='',
                              examples=['Processing download'])
    percent_complete: int = pydantic.Field(description='The current percentage of task completion',
                                           default=0,
                                           examples=[50])


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
