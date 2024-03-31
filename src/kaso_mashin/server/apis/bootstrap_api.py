import typing
import uuid

import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import ExceptionSchema
from kaso_mashin.common.ddd_scaffold import EntityNotFoundException
from kaso_mashin.common.entities import (
    BootstrapEntity,
    BootstrapListSchema, BootstrapGetSchema, BootstrapCreateSchema, BootstrapModifySchema
)


class BootstrapAPI(AbstractAPI):
    """
    The Bootstrap API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(tags=['bootstraps'],
                                         responses={
                                             404: {'model': ExceptionSchema,
                                                   'description': 'Bootstrap template not found'},
                                             400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route(path='/',
                                   endpoint=self.list,
                                   methods=['GET'],
                                   summary='List bootstrap templates',
                                   description='List all currently known bootstrap templates',
                                   response_description='The list of currently known bootstrap templates',
                                   status_code=200,
                                   responses={200: {'model': BootstrapListSchema}})

    async def list(self):
        entities = await self._runtime.bootstrap_repository.list()
        return [BootstrapListSchema.model_validate(e) for e in entities]

    async def get(self,
                  uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Bootstrap Template UUID',
                                                                description='The unique bootstrap template Id',
                                                                examples=[
                                                                    '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._runtime.bootstrap_repository.get_by_uid(uid)
        return BootstrapGetSchema.model_validate(entity)

    async def create(self, schema: BootstrapCreateSchema):
        entity = await BootstrapEntity.create(name=schema.name,
                                              kind=schema.kind,
                                              content=schema.content)
        return BootstrapGetSchema.model_validate(entity)

    async def modify(self,
                     uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Bootstrap template UUID',
                                                                   description='The unique bootstrap template Id',
                                                                   examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                     schema: BootstrapModifySchema):
        entity = await self._runtime.bootstrap_repository.get_by_uid(uid)
        await entity.modify(name=schema.name,
                            kind=schema.kind,
                            content=schema.content)
        return BootstrapGetSchema.model_validate(entity)

    async def remove(self,
                     uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Bootstrap template UUID',
                                                                   description='The unique bootstrap template Id',
                                                                   examples=[
                                                                       '4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                     response: fastapi.Response):
        try:
            entity = await self._runtime.bootstrap_repository.get_by_uid(uid)
            await entity.remove()
            response.status_code = 204
        except EntityNotFoundException:
            response.status_code = 410
        return response
