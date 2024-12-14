"""
The Bootstrap API
"""

from typing import Annotated
from uuid import UUID

import fastapi

from kaso_mashin.base import EntityNotFoundException
from kaso_mashin.domain import (
    Bootstrap,
    BootstrapListSchema,
    BootstrapGetSchema,
    BootstrapCreateSchema,
    BootstrapModifySchema)

router = fastapi.APIRouter(tags=['bootstrap'])

@router.get(path='/',
            summary='List bootstraps',
            description='List all bootstraps',
            response_description='A list of bootstraps',
            status_code=200,
            responses={200: {'model': BootstrapListSchema}})
async def bootstrap_list():
    entities = await Bootstrap.repository.list()
    return BootstrapListSchema(entries=[BootstrapGetSchema.model_validate(e) for e in entities])


@router.get(path='/{uid}',
            summary='Get a bootstrap by its unique id',
            description='Get details about a bootstrap',
            response_description='A bootstrap',
            status_code=200,
            response_model=BootstrapGetSchema)
async def bootstrap_get(uid: Annotated[UUID, fastapi.Path(description='The bootstrap UUID')]):
    bootstrap = await Bootstrap.repository.get_by_uid(uid)
    if not bootstrap:
        raise EntityNotFoundException(status=404, msg='No such bootstrap')
    return BootstrapGetSchema.model_validate(bootstrap)

@router.post(path='/',
             summary='Create a bootstrap',
             description='Create a new bootstrap',
             response_description='The created bootstrap',
             status_code=201,
             response_model=BootstrapGetSchema)
async def bootstrap_create(schema: BootstrapCreateSchema):
    bootstrap = Bootstrap(name=schema.name, kind=schema.kind, content=schema.content)
    await bootstrap.save()
    return BootstrapGetSchema.model_validate(bootstrap)

@router.put(path='/{uid}',
            summary='Modify a bootstrap',
            description='Modify the permitted fields of an existing bootstrap',
            response_description='The modified bootstrap',
            status_code=200,
            response_model=BootstrapGetSchema)
async def bootstrap_modify(uid: Annotated[UUID, fastapi.Path(description='The bootstrap UUID')],
                           schema: BootstrapModifySchema):
    bootstrap = await Bootstrap.repository.get_by_uid(uid)
    bootstrap.name = schema.name
    bootstrap.content = schema.content
    await bootstrap.save()
    return BootstrapGetSchema.model_validate(bootstrap)

@router.delete(path='/{uid}',
               summary='Remove a bootstrap',
               description='Permanently remove a bootstrap',
               response_description='There is no response content',
               responses={
                   204: {'model': None, 'description': 'The bootstrap was removed'},
                   410: {'model': None, 'description': 'The bootstrap was already gone'}
               })
async def bootstrap_remove(uid: Annotated[UUID, fastapi.Path(description='The bootstrap UUID')],
                           response: fastapi.Response):
    try:
        bootstrap = await Bootstrap.repository.get_by_uid(uid)
        await bootstrap.remove()
        response.status_code = 204
    except EntityNotFoundException:
        response.status_code = 410
    return response
