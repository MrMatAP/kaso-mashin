import typing
import uuid
import pathlib

import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import ExceptionSchema
from kaso_mashin.common.entities import (
    DiskEntity,
    DiskListSchema, DiskGetSchema, DiskCreateSchema, DiskModifySchema
)


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
                                   responses={200: {'model': typing.List[DiskListSchema]}})
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.get_disk,
                                   methods=['GET'],
                                   summary='Get a disk',
                                   description='Get information about a disk specified by its unique ID',
                                   response_description='A disk',
                                   status_code=200,
                                   response_model=DiskGetSchema)
        self._router.add_api_route(path='/',
                                   endpoint=self.create_disk,
                                   methods=['POST'],
                                   summary='Create a disk',
                                   description='Create a new disk',
                                   response_description='The created disk',
                                   status_code=201,
                                   response_model=DiskGetSchema)
        self._router.add_api_route('/{uid}', self.modify_disk, methods=['PUT'],
                                   summary='Modify a disk',
                                   description='This will update the permissible fields of a disk',
                                   response_description='The updated disk',
                                   status_code=200,
                                   response_model=DiskGetSchema)
        self._router.add_api_route('/{uid}', self.remove_disk, methods=['DELETE'],
                                   summary='Remove a disk',
                                   description='Remove a disk. This will irrevocably and permanently delete the disk',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

    async def list_disks(self):
        entities = await self._runtime.disk_aggregate_root.list(force_reload=True)
        return [DiskListSchema.model_validate(e) for e in entities]

    async def get_disk(self,
                       uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                     description='The unique disk Id',
                                                                     examples=[
                                                                         '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._runtime.disk_aggregate_root.get(uid)
        return DiskGetSchema.model_validate(entity)

    async def create_disk(self, schema: DiskCreateSchema):
        image = None
        if schema.image_uid is not None:
            image = await self._runtime.image_aggregate_root.get(schema.image_uid)
        entity = await DiskEntity.create(owner=self._runtime.disk_aggregate_root,
                                         name=schema.name,
                                         path=pathlib.Path(schema.path),
                                         size=schema.size,
                                         disk_format=schema.disk_format,
                                         image=image)
        return DiskGetSchema.model_validate(entity)

    async def modify_disk(self,
                          uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                        description='The unique disk Id',
                                                                        examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                          schema: DiskModifySchema):
        entity = await self._runtime.disk_aggregate_root.get(uid)
        if entity.size != schema.size:
            entity = await entity.resize(schema.size)
        return DiskGetSchema.model_validate(entity)

    async def remove_disk(self,
                          uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                        description='The unique disk Id',
                                                                        examples=[
                                                                            '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._runtime.disk_aggregate_root.get(uid)
        await entity.remove()
