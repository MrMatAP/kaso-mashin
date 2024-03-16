import typing
import uuid

import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import ExceptionSchema
from kaso_mashin.common.entities import (
    NetworkEntity,
    NetworkListSchema, NetworkGetSchema, NetworkCreateSchema, NetworkModifySchema
)


class NetworkAPI(AbstractAPI):
    """
    The Network API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['networks'],
            responses={
                404: {'model': ExceptionSchema, 'description': 'Network not found'},
                400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route(path='/',
                                   endpoint=self.list_networks,
                                   methods=['GET'],
                                   summary='List networks',
                                   description='List all currently known networks',
                                   response_description='The list of currently known networks',
                                   status_code=200,
                                   responses={
                                       200: {'model': typing.List[NetworkListSchema]}})
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.get_network,
                                   methods=['GET'],
                                   summary='Get a network',
                                   description='Get full information about a network specified by its unique ID.',
                                   response_description='A network',
                                   status_code=200,
                                   response_model=NetworkGetSchema)
        self._router.add_api_route(path='/',
                                   endpoint=self.create_network,
                                   methods=['POST'],
                                   summary='Create a network',
                                   description='Create a new network',
                                   response_description='The newly created network',
                                   status_code=201,
                                   response_model=NetworkGetSchema)
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.modify_network,
                                   methods=['PUT'],
                                   summary='Modify a network',
                                   description='This will update the permissible fields of a network based on the '
                                               'provided input.',
                                   response_description='The updated network',
                                   status_code=200,
                                   response_model=NetworkGetSchema)
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.remove_network,
                                   methods=['DELETE'],
                                   summary='Remove a network',
                                   description='Remove the specified network. This will irrevocably and permanently '
                                               'delete the network.',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

    async def list_networks(self):
        entities = await self._runtime.network_repository.list()
        return [NetworkListSchema.model_validate(e) for e in entities]

    async def get_network(self,
                          uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Network UUID',
                                                                        description='The unique disk Id',
                                                                        examples=[
                                                                            '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._runtime.network_repository.get_by_uid(uid)
        return NetworkGetSchema.model_validate(entity)

    async def create_network(self, schema: NetworkCreateSchema):
        entity = await NetworkEntity.create(name=schema.name,
                                            kind=schema.kind,
                                            cidr=schema.cidr,
                                            gateway=schema.gateway)
        return NetworkGetSchema.model_validate(entity)

    async def modify_network(self,
                             uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Network UUID',
                                                                           description='The unique disk Id',
                                                                           examples=[
                                                                               '4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                             schema: NetworkModifySchema):
        entity = await self._runtime.network_repository.get_by_uid(uid)
        await entity.modify(name=schema.name,
                            cidr=schema.cidr,
                            gateway=schema.gateway)
        return NetworkGetSchema.model_validate(entity)

    async def remove_network(self,
                             uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Network UUID',
                                                                           description='The unique disk Id',
                                                                           examples=[
                                                                               '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._runtime.network_repository.get_by_uid(uid)
        await entity.remove()
