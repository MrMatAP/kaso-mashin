import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import ExceptionSchema, NetworkModel, NetworkSchema, NetworkCreateSchema, NetworkModifySchema


class NetworkAPI(AbstractAPI):
    """
    The network API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['networks'],
            responses={
                404: {'model': ExceptionSchema, 'description': 'Network not found'},
                400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route('/', self.list_networks, methods=['GET'],
                                   summary='List networks',
                                   description='List all known networks. You can optionally filter the list by the'
                                               '"name" query parameter. If you do filter using the "name" query '
                                               'parameter then the corresponding single network is returned.',
                                   response_description='A list of networks, or a single network when filtered by name',
                                   status_code=200,
                                   responses={
                                       200: {'model': typing.Union[typing.List[NetworkSchema], NetworkSchema]}})
        self._router.add_api_route('/{network_id}', self.get_network, methods=['GET'],
                                   summary='Get a network',
                                   description='Get full information about a network specified by its unique ID.',
                                   response_description='A network',
                                   status_code=200,
                                   response_model=NetworkSchema)
        self._router.add_api_route('/', self.create_network, methods=['POST'],
                                   summary='Create a network',
                                   description='Create a new network',
                                   response_description='The newly created network',
                                   status_code=201,
                                   response_model=NetworkSchema)
        self._router.add_api_route('/{network_id}', self.modify_network, methods=['PUT'],
                                   summary='Modify a network',
                                   description='This will update the permissible fields of a network based on the '
                                               'provided input.',
                                   response_description='The updated network',
                                   status_code=200,
                                   response_model=NetworkSchema)
        self._router.add_api_route('/{network_id}', self.remove_network, methods=['DELETE'],
                                   summary='Remove a network',
                                   description='Remove the specified network. This will irrevocably and permanently '
                                               'delete the network.',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

    async def list_networks(self,
                            name: typing.Annotated[str | None,
                                                   fastapi.Query(title='Network name',
                                                                 description='A unique network name',
                                                                 examples=['mrmat-shared'])] = None):
        if name:
            return self.network_controller.get(name=name)
        return self.network_controller.list()

    async def get_network(self,
                          network_id: typing.Annotated[int, fastapi.Path(title='Network ID',
                                                                         description='A unique network ID',
                                                                         examples=[1])]):
        network = self.network_controller.get(network_id=network_id)
        return network or fastapi.responses.JSONResponse(status_code=404,
                                                         content=ExceptionSchema(
                                                             status=404,
                                                             msg='No such network could be found')
                                                         .model_dump())

    async def create_network(self, schema: NetworkCreateSchema):
        model = self.network_controller.create(NetworkModel.from_schema(schema))
        return model

    async def modify_network(self,
                             network_id: typing.Annotated[int, fastapi.Path(title='Network ID',
                                                                            description='The network ID to modify',
                                                                            examples=[1])],
                             schema: NetworkModifySchema):
        return self.network_controller.modify(network_id=network_id, update=NetworkModel.from_schema(schema))

    async def remove_network(self,
                             network_id: typing.Annotated[int, fastapi.Path(title='Network ID',
                                                                            description='The network ID to remove',
                                                                            examples=[1])],
                             response: fastapi.Response):
        gone = self.network_controller.remove(network_id)
        response.status_code = 410 if gone else 204
        return response
