"""
The Image API
"""

from typing import Annotated
from uuid import UUID
import datetime

import fastapi

from kaso_mashin.base import EntityNotFoundException
from kaso_mashin.domain import (
    Image,
    ImageListSchema,
    ImageGetSchema,
    ImageCreateSchema,
    ImageModifySchema)
from kaso_mashin.services import Task, TaskRelation, TaskGetSchema

router = fastapi.APIRouter(tags=['image'])

@router.get(path='/',
            summary='List images',
            description='List all images',
            response_description='A list of images',
            status_code=200,
            responses={200: {'model': ImageListSchema}})
async def image_list():
    entities = await Image.repository.list()
    return ImageListSchema(entries=[ImageGetSchema.model_validate(e) for e in entities])

@router.get(path='/{uid}',
            summary='Get an image by its unique id',
            description='Get details about an image',
            response_description='An image',
            status_code=200,
            response_model=ImageGetSchema)
async def image_get(uid: Annotated[UUID, fastapi.Path(description='The image UUID')]):
    image = await Image.repository.get_by_uid(uid)
    if not image:
        raise EntityNotFoundException(status=404, msg='No such image')
    return ImageGetSchema.model_validate(image)

@router.post(path='/',
             summary='Create an image',
             description='Create a new image',
             response_description='The created image',
             status_code=201,
             response_model=TaskGetSchema)
async def image_create(schema: ImageCreateSchema,
                       background_tasks: fastapi.BackgroundTasks):
    image = Image(name=schema.name, url=schema.url)
    image.min_vcpu = schema.min_vcpu
    image.min_ram = schema.min_ram
    task = await image.save()
    background_tasks.add_task(task.run)
    return TaskGetSchema.model_validate(task)


@router.put(path='/{uid}',
            summary='Modify an image',
            description='Modify the permitted fields of an existing image',
            response_description='The modified image',
            status_code=200,
            response_model=ImageGetSchema)
async def image_modify(uid: Annotated[UUID, fastapi.Path(description='The image UUID')],
                       schema: ImageModifySchema):
    image = await Image.repository.get_by_uid(uid)
    image.name = schema.name
    image.min_vcpu = schema.min_vcpu
    image.min_ram = schema.min_ram
    image.min_disk = schema.min_disk
    await image.save()
    return ImageGetSchema.model_validate(image)

@router.delete(path='/{uid}',
               summary='Remove an image',
               description='Permanently remove an image',
               response_description='There is no response content',
               responses={
                   204: {'model': None, 'description': 'The image was removed'},
                   410: {'model': None, 'description': 'The image was already gone'}
               })
async def image_remove(uid: Annotated[UUID, fastapi.Path(description='The image UUID')],
                           response: fastapi.Response):
    try:
        image = await Image.repository.get_by_uid(uid)
        await image.remove()
        response.status_code = 204
    except EntityNotFoundException:
        response.status_code = 410
    return response
