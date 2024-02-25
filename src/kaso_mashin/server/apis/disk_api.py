import typing
import uuid
import pathlib

import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import ExceptionSchema
from kaso_mashin.common.entities.disks import DiskEntity, DiskModel, DiskAggregateRoot, DiskListSchema, \
    DiskCreateSchema, DiskGetSchema, DiskModifySchema


class DiskAPI(AbstractAPI):
    """
    The Disk API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._disk_aggregate_root = None
        self._router = fastapi.APIRouter(tags=['disks'],
                                         responses={
                                             404: {'model': ExceptionSchema, 'description': 'Disk not found'},
                                             400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route(path='/',
                                   endpoint=self.list_disks,
                                   methods=['GET'],
                                   summary='List disks',
                                   description='List all currently known disks',
                                   response_description='The list of currently known disks',
                                   status_code=200,
                                   responses={200: {'model': typing.List[DiskListSchema]}},
                                   dependencies=[fastapi.Depends(self.disk_aggregate_root)])
        self._router.add_api_route('/{uid}', self.get_disk, methods=['GET'],
                                   summary='Get a disk',
                                   description='Get full information about a disk specified by its unique ID.',
                                   response_description='A disk',
                                   status_code=200,
                                   response_model=DiskGetSchema,
                                   dependencies=[fastapi.Depends(self.disk_aggregate_root)])
        self._router.add_api_route('/', self.create_disk, methods=['POST'],
                                   summary='Create a disk',
                                   description='This will create a disk based on the provided input.',
                                   response_description='The created disk',
                                   status_code=201,
                                   response_model=DiskGetSchema,
                                   dependencies=[fastapi.Depends(self.disk_aggregate_root)])
        self._router.add_api_route('/{uid}', self.modify_disk, methods=['PUT'],
                                   summary='Modify a disk',
                                   description='This will update the permissible fields of a disk based on the '
                                               'provided input',
                                   response_description='The updated identity',
                                   status_code=200,
                                   response_model=DiskGetSchema,
                                   dependencies=[fastapi.Depends(self.disk_aggregate_root)])
        self._router.add_api_route('/{uid}', self.remove_disk, methods=['DELETE'],
                                   summary='Remove a disk',
                                   description='Remove a disk. This will irrevocably and permanently delete the disk',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}},
                                   dependencies=[fastapi.Depends(self.disk_aggregate_root)])

    async def disk_aggregate_root(self) -> DiskAggregateRoot:
        if self._disk_aggregate_root is None:
            self._disk_aggregate_root = DiskAggregateRoot(model=DiskModel,
                                                          session_maker=await self._runtime.db.async_sessionmaker)
        return self._disk_aggregate_root

    async def list_disks(self):
        entities = await self._disk_aggregate_root.list(force_reload=True)
        return [DiskListSchema.model_validate(e) for e in entities]

    async def get_disk(self,
                       uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                     description='The unique disk Id',
                                                                     examples=[
                                                                         '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._disk_aggregate_root.get(uid)
        return DiskGetSchema.model_validate(entity)

    async def create_disk(self, schema: DiskCreateSchema):
        entity = await DiskEntity.create(owner=self._disk_aggregate_root,
                                         name=schema.name,
                                         path=pathlib.Path(schema.path),
                                         size=schema.size,
                                         disk_format=schema.disk_format)
        return DiskGetSchema.model_validate(entity)

    async def modify_disk(self,
                          uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                        description='The unique disk Id',
                                                                        examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                          schema: DiskModifySchema):
        entity = await self._disk_aggregate_root.get(uid)
        if entity.size != schema.size:
            entity = await entity.resize(schema.size)
        return DiskGetSchema.model_validate(entity)

    async def remove_disk(self,
                          uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                        description='The unique disk Id',
                                                                        examples=[
                                                                            '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._disk_aggregate_root.get(uid)
        await entity.remove()
