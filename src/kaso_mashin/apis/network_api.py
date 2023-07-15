import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import ExceptionSchema, NetworkSchema, NetworkCreateSchema


class NetworkAPI(AbstractAPI):
    """
    The network API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['networks'],
            responses={
                fastapi.status.HTTP_404_NOT_FOUND: {'model': ExceptionSchema, 'description': 'Image not found'},
                fastapi.status.HTTP_400_BAD_REQUEST: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route('/', self.list_networks,
                                   methods=['GET'],
                                   summary='List known networks',
                                   description='List all known networks. You can optionally filter the list by the '
                                               '"name" query parameter',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {
                                           'model': typing.Union[typing.List[NetworkSchema], NetworkSchema]
                                       }})
        self._router.add_api_route('/{network_id}', self.get_network,
                                   methods=['GET'],
                                   summary='Get a network by its unique id',
                                   description='Get full information about a network specified by its unique id',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {'model': NetworkSchema}})
        self._router.add_api_route('/{network_id}', self.create_network,
                                   methods=['POST'],
                                   summary='Create a network',
                                   description='Create a network',
                                   responses={
                                       fastapi.status.HTTP_201_CREATED: {'model': NetworkSchema}})
        self._router.add_api_route('/{network_id}', self.modify_network,
                                   methods=['PUT'],
                                   summary='Modify a network',
                                   description='Modify a network',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {'model': NetworkSchema}})
        self._router.add_api_route('/{network_id}', self.remove_network,
                                   methods=['DELETE'],
                                   summary='Remove a network',
                                   description='Remove a network',
                                   responses={
                                       fastapi.status.HTTP_204_NO_CONTENT: {'model': None},
                                       fastapi.status.HTTP_410_GONE: {'model': None}})

    async def list_networks(self,
                            name: typing.Annotated[str | None, fastapi.Query(description='The network name')] = None):
        if name:
            return self.network_controller.get(name=name)
        return self.network_controller.list()

    async def get_network(self,
                          network_id: typing.Annotated[int, fastapi.Path(description='The unique network id')]):
        network = self.network_controller.get(network_id=network_id)
        return network or fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_404_NOT_FOUND,
                                                         content=ExceptionSchema(
                                                             status=fastapi.status.HTTP_404_NOT_FOUND,
                                                             msg='No such network could be found')
                                                         .model_dump())

    async def create_network(self, schema: NetworkCreateSchema):
        return fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                              content=ExceptionSchema(status=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                                                      msg='Not yet implemented').model_dump())

    async def modify_network(self,
                             network_id: typing.Annotated[
                                 int, fastapi.Path(description='The unique network id to modify')],
                             schema: NetworkSchema):
        return fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                              content=ExceptionSchema(status=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                                                      msg='Not yet implemented').model_dump())

    async def remove_network(self,
                             network_id: typing.Annotated[int, fastapi.Path(description='The network id to remove')],
                             response: fastapi.Response):
        gone = self.network_controller.remove(network_id)
        response.status_code = fastapi.status.HTTP_410_GONE if gone else fastapi.status.HTTP_204_NO_CONTENT
        return response
