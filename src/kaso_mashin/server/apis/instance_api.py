import uuid
import typing
import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import ExceptionSchema
from kaso_mashin.common.ddd_scaffold import EntityNotFoundException
from kaso_mashin.common.entities import (
    InstanceEntity, InstanceListSchema, InstanceGetSchema, InstanceCreateSchema, InstanceModifySchema,
    TaskEntity, TaskGetSchema,
    ImageEntity,
    NetworkEntity
)


class InstanceAPI(AbstractAPI):
    """
    The Instance API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['instances'],
            responses={
                404: {'model': ExceptionSchema, 'description': 'Instance not found'},
                400: {'model': ExceptionSchema, 'description': 'Incorrect input'}
            })
        self._router.add_api_route(path='/',
                                   endpoint=self.list_instances,
                                   methods=['GET'],
                                   summary='List instances',
                                   description='List all known instances',
                                   response_description='The list of currently known instances',
                                   status_code=200,
                                   responses={200: {'model': typing.List[InstanceListSchema]}})
        self._router.add_api_route('/{uid}',
                                   endpoint=self.get_instance,
                                   methods=['GET'],
                                   summary='Get an instance',
                                   description='Get full information about an instance specified by its unique ID.',
                                   response_description='An instance',
                                   status_code=200,
                                   response_model=InstanceGetSchema)
        self._router.add_api_route(path='/',
                                   endpoint=self.create_instance,
                                   methods=['POST'],
                                   summary='Create an instance',
                                   description='Creating an instance is an asynchronous operation, you will get a task '
                                               'object back which you can subsequently check for progress using the '
                                               'task API',
                                   response_description='A task',
                                   status_code=201,
                                   responses={
                                       201: {'model': TaskGetSchema, 'description': 'Instance is being created'},
                                       404: {'model': ExceptionSchema, 'description': 'Image or network not found'}
                                   })
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.modify_instance,
                                   methods=['PUT'],
                                   summary='Modify an instance',
                                   description='This will update the permissible fields of an image based on the '
                                               'provided input.',
                                   response_description='The updated instance',
                                   status_code=200,
                                   response_model=TaskGetSchema)
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.remove_instance,
                                   methods=['DELETE'],
                                   summary='Remove an instance',
                                   description='Remove the specified image. This will irrevocably and permanently '
                                               'delete the image.',
                                   response_description='there is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

    async def list_instances(self):
        """
        List instances
        """
        entities = await self._runtime.instance_repository.list()
        return [InstanceListSchema.model_validate(e) for e in entities]

    async def get_instance(self,
                           uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Instance UUID',
                                                                         description='The unique instance Id',
                                                                         examples=[
                                                                             '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._runtime.instance_repository.get_by_uid(uid)
        return InstanceGetSchema.model_validate(entity)

    async def create_instance(self, schema: InstanceCreateSchema, background_tasks: fastapi.BackgroundTasks):
        try:
            image = await ImageEntity.repository.get_by_uid(schema.image_uid)
            network = await NetworkEntity.repository.get_by_uid(schema.network_uid)
            task = await TaskEntity.create(name=f'Creating instance {schema.name}')
            instance_path = self._runtime.config.instances_path / schema.name
            background_tasks.add_task(InstanceEntity.create,
                                      task=task,
                                      user=self._runtime.owning_user,
                                      name=schema.name,
                                      path=instance_path,
                                      uefi_code=self._runtime.uefi_code_path,
                                      uefi_vars=self._runtime.uefi_vars_path,
                                      vcpu=schema.vcpu,
                                      ram=schema.ram,
                                      image=image,
                                      os_disk_size=schema.os_disk_size,
                                      network=network)
            return TaskGetSchema.model_validate(task)
        except EntityNotFoundException as e:
            return ExceptionSchema.model_validate(e)

    async def modify_instance(self,
                              uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Instance UUID',
                                                                            description='The unique instance Id',
                                                                            examples=[
                                                                                '4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                              schema: InstanceModifySchema,
                              background_tasks: fastapi.BackgroundTasks):
        entity = await self._runtime.instance_repository.get_by_uid(uid)
        task = TaskEntity.create(f'Modifying instance {entity.name}')
        background_tasks.add_task(entity.modify,
                                  task=task)
        return TaskGetSchema.model_validate(task)

    async def remove_instance(self,
                              uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Instance UUID',
                                                                            description='The unique instance Id',
                                                                            examples=[
                                                                                '4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                              response: fastapi.Response):
        try:
            entity = await self._runtime.instance_repository.get_by_uid(uid)
            await entity.remove()
            response.status_code = 204
        except EntityNotFoundException:
            response.status_code = 410
        return response
