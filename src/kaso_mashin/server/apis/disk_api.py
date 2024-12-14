"""
The Disk API
"""

from typing import Annotated
from uuid import UUID
import pathlib

import fastapi

from kaso_mashin.base import EntityNotFoundException
from kaso_mashin.domain import (
    Disk,
    DiskListSchema,
    DiskGetSchema,
    DiskCreateSchema,
    DiskModifySchema,
    Image)

router = fastapi.APIRouter(tags=['disk'])

@router.get(path='/',
            summary='List disks',
            description='List all disks',
            response_description='A list of disks',
            status_code=200,
            responses={200: {'model': DiskListSchema}})
async def disk_list():
    entities = await Disk.repository.list()
    return DiskListSchema(entries=[DiskGetSchema.model_validate(e) for e in entities])

@router.get(path='/{uid}',
            summary='Get a disk by its unique id',
            description='Get details about a disk',
            response_description='A disk',
            status_code=200,
            response_model=DiskGetSchema)
async def disk_get(uid: Annotated[UUID, fastapi.Path(description='The disk UUID')]):
    entity = await Disk.repository.get_by_uid(uid)
    if not entity:
        raise EntityNotFoundException(status=404, msg='No such disk')
    return DiskGetSchema.model_validate(entity)

@router.post(path='/',
             summary='Create a disk',
             description='Create a new disk',
             response_description='The created disk',
             status_code=201,
             response_model=DiskGetSchema)
async def disk_create(schema: DiskCreateSchema):
    image = None
    if schema.image_uid is not None:
        image = await Image.repository.get_by_uid(schema.image_uid)
    disk = Disk(
        name=schema.name,
        path=pathlib.Path(schema.path),
        size=schema.size,
        disk_format=schema.disk_format,
        image=image)
    await disk.save()
    return DiskGetSchema.model_validate(disk)

@router.put(path='/{uid}',
            summary='Modify a disk',
            description='Modify the permitted fields of an existing disk',
            response_description='The modified disk',
            status_code=200,
            response_model=DiskGetSchema)
async def disk_modify(uid: Annotated[UUID, fastapi.Path(description='The disk UUID')],
                      schema: DiskModifySchema):
    entity: Disk = await Disk.repository.get_by_uid(uid)
    if entity.size != schema.size:
        entity = await entity.resize(schema.size)
    return DiskGetSchema.model_validate(entity)

@router.delete(path='/{uid}',
               summary='Remove a disk',
               description='Permanently remove a disk',
               response_description='There is no response content',
               responses={
                   204: {'model': None, 'description': 'The disk was removed'},
                   410: {'model': None, 'description': 'The disk was already gone'}
               })
async def identity_remove(uid: Annotated[UUID, fastapi.Path(description='The disk UUID')],
                          response: fastapi.Response):
    try:
        disk = await Disk.repository.get_by_uid(uid)
        await disk.remove()
        response.status_code = 204
    except EntityNotFoundException:
        response.status_code = 410
    return response
