import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import ExceptionSchema, InstanceSchema, InstanceCreateSchema, TaskSchema


class InstanceAPI(AbstractAPI):
    """
    The instance API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['instances'],
            responses={
                fastapi.status.HTTP_404_NOT_FOUND: {'model': ExceptionSchema, 'description': 'Instance not found'},
                fastapi.status.HTTP_400_BAD_REQUEST: {'model': ExceptionSchema, 'description': 'Incorrect input'}
            })
        self._router.add_api_route('/', self.list_instances,
                                   methods=['GET'],
                                   summary='List known instances',
                                   description='List all known instances. You can optionally filter the list using'
                                               'the "name" query parameter',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {
                                           'model': typing.Union[typing.List[InstanceSchema], InstanceSchema]}
                                   })
        self._router.add_api_route('/{instance_id}', self.get_instance,
                                   methods=['GET'],
                                   summary='Get an instance by its unique id',
                                   description='Get full information about an instance specified by its unique id',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {'model': InstanceSchema}
                                   })
        # TODO: Start/Stop
        self._router.add_api_route('/{instance_id}', self.remove_instance,
                                   methods=['DELETE'],
                                   summary='Remove an instance',
                                   description='Remove an instance specified by its unique id',
                                   responses={
                                       fastapi.status.HTTP_204_NO_CONTENT: {'model': None},
                                       fastapi.status.HTTP_410_GONE: {'model': None}
                                   })

    async def list_instances(self,
                             name: typing.Annotated[str | None, fastapi.Query(description='The instance name')] = None):
        """
        List instances
        """
        if name:
            return self.instance_controller.get(name=name)
        return self.instance_controller.list()

    async def get_instance(self,
                           instance_id: typing.Annotated[int, fastapi.Path(description='The unique instance id')]):
        """
        Return an instance by its id
        """
        instance = self.instance_controller.get(instance_id=instance_id)
        return instance or fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_404_NOT_FOUND,
                                                          content=ExceptionSchema(
                                                              status=fastapi.status.HTTP_404_NOT_FOUND,
                                                              msg='No such instance could be found')
                                                          .model_dump())

    async def create_instance(self):
        pass

    async def remove_instance(self):
        pass

    async def start_instance(self):
        pass

    async def stop_instance(self):
        pass
