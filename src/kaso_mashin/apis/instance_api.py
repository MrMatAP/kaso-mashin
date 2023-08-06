import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import (
    ExceptionSchema, TaskSchema,
    InstanceModel,
    InstanceSchema, InstanceCreateSchema, InstanceModifySchema )


class InstanceAPI(AbstractAPI):
    """
    The instance API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['instances'],
            responses={
                404: {'model': ExceptionSchema, 'description': 'Instance not found'},
                400: {'model': ExceptionSchema, 'description': 'Incorrect input'}
            })
        self._router.add_api_route('/', self.list_instances, methods=['GET'],
                                   summary='List instances',
                                   description='List all known instances. You can optionally filter the list by the'
                                               '"name" query parameter. If you do filter using the "name" query '
                                               'parameter then the corresponding single instance is returned.',
                                   response_description='A list of instance, or a single instance when filtered by '
                                                        'name',
                                   status_code=200,
                                   responses={200: {'model': typing.Union[typing.List[InstanceSchema], InstanceSchema]}
                                   })
        self._router.add_api_route('/{instance_id}', self.get_instance, methods=['GET'],
                                   summary='Get an instance',
                                   description='Get full information about an instance specified by its unique ID.',
                                   response_description='An instance',
                                   status_code=200,
                                   response_model=InstanceSchema)
        self._router.add_api_route('/', self.create_instance, methods=['POST'],
                                   summary='Create an instance',
                                   description='Creating an instance is an asynchronous operation, you will get a task '
                                               'object back which you can subsequently check for progress using the '
                                               'task API',
                                   response_description='A task',
                                   status_code=201,
                                   response_model=TaskSchema)
        self._router.add_api_route('/{instance_id}', self.modify_instance, methods=['PUT'],
                                   summary='Modify an instance',
                                   description='This will update the permissible fields of an image based on the '
                                               'provided input.',
                                   response_description='The updated instance',
                                   status_code=200,
                                   response_model=InstanceSchema)
        self._router.add_api_route('/{instance_id}', self.remove_instance, methods=['DELETE'],
                                   summary='Remove an instance',
                                   description='Remove the specified image. This will irrevocably and permanently '
                                               'delete the image.',
                                   response_description='there is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

        self._router.add_api_route('/{instance_id}/state', self.start_instance, methods=['POST'],
                                   summary='Start the instance',
                                   description='This is an asynchronous operation, you will get a'
                                               'task object back which you can subsequently check for progress using'
                                               'the task api',
                                   response_description='A task',
                                   response_model=TaskSchema)
        self._router.add_api_route('/{instance_id}/state', self.stop_instance, methods=['DELETE'],
                                   summary='Stop the instance',
                                   description='This is an asynchronous operation, you will get a'
                                           'task object back which you can subsequently check for progress using'
                                           'the task api',
                                   response_description='A task',
                                   response_model=TaskSchema)

    async def list_instances(self,
                             name: typing.Annotated[str | None, fastapi.Query(title='Instance name',
                                                                              description='The instance name',
                                                                              examples=[1])] = None):
        """
        List instances
        """
        if name:
            return self.instance_controller.get(name=name)
        return self.instance_controller.list()

    async def get_instance(self,
                           instance_id: typing.Annotated[int, fastapi.Path(title='Instance ID',
                                                                           description='The unique instance id',
                                                                           examples=[1])]):
        """
        Return an instance by its id
        """
        instance = self.instance_controller.get(instance_id=instance_id)
        return instance or fastapi.responses.JSONResponse(status_code=404,
                                                          content=ExceptionSchema(
                                                              status=410,
                                                              msg='No such instance could be found')
                                                          .model_dump())

    async def create_instance(self, schema: InstanceCreateSchema, background_tasks: fastapi.BackgroundTasks):
        task = self.task_controller.create(name=f'Creating instance {schema.name}')
        background_tasks.add_task(self.instance_controller.create,
                                  model=InstanceModel.from_schema(schema),
                                  task=task)
        return task

    async def modify_instance(self,
                              instance_id: typing.Annotated[int, fastapi.Path(title='Instance ID',
                                                                              description='The instance ID to modify',
                                                                              examples=[1])],
                              schema: InstanceModifySchema):
        return self.instance_controller.modify(instance_id=instance_id,
                                               update=InstanceModel.from_schema(schema))

    async def remove_instance(self,
                              instance_id: typing.Annotated[int, fastapi.Path(title='Instance ID',
                                                                              description='The instance ID to remove',
                                                                              examples=[1])],
                              response: fastapi.Response):
        gone = self.instance_controller.remove(instance_id)
        response.status_code = 410 if gone else 204
        return response

    async def start_instance(self):
        return fastapi.responses.JSONResponse(status_code=510,
                                              content=ExceptionSchema(status=510,
                                                                      msg='Not yet implemented')
                                              .model_dump())

    async def stop_instance(self):
        return fastapi.responses.JSONResponse(status_code=510,
                                              content=ExceptionSchema(status=510,
                                                                      msg='Not yet implemented')
                                              .model_dump())
