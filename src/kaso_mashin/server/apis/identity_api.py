"""
The Identity API
"""

from typing import Annotated
from uuid import UUID

import fastapi

from kaso_mashin.base import EntityNotFoundException
from kaso_mashin.domain import (
    Identity,
    IdentityListSchema,
    IdentityGetSchema,
    IdentityCreateSchema,
    IdentityModifySchema)

router = fastapi.APIRouter(tags=['identity'])

@router.get(path='/',
            summary='List identities',
            description='List all identities',
            response_description='A list of identities',
            status_code=200,
            responses={200: {'model': IdentityListSchema}})
async def identity_list():
    entities = await Identity.repository.list()
    return IdentityListSchema(entries=[IdentityGetSchema.model_validate(e) for e in entities])

@router.get(path='/{uid}',
            summary='Get an identity by its unique id',
            description='Get details about an identity',
            response_description='An identity',
            status_code=200,
            response_model=IdentityGetSchema)
async def identity_get(uid: Annotated[UUID, fastapi.Path(description='The identity UUID')]):
    entities = await Identity.repository.list()
    return IdentityListSchema(entries=[IdentityListSchema.model_validate(e) for e in entities])

@router.post(path='/',
             summary='Create an identity',
             description='Create a new identity',
             response_description='The created identity',
             status_code=201,
             response_model=IdentityGetSchema)
async def identity_create(schema: IdentityCreateSchema):
    identity = Identity(name=schema.name, kind=schema.kind)
    identity.gecos = schema.gecos
    identity.homedir = schema.homedir
    identity.shell = schema.shell
    identity.credential = schema.credential
    await identity.save()
    return IdentityGetSchema.model_validate(identity)

@router.put(path='/{uid}',
            summary='Modify an identity',
            description='Modify the permitted fields of an existing identity',
            response_description='The modified identity',
            status_code=200,
            response_model=IdentityGetSchema)
async def identity_modify(uid: Annotated[UUID, fastapi.Path(description='The identity UUID')],
                          schema: IdentityModifySchema):
    identity = await Identity.repository.get_by_uid(uid)
    identity.gecos = schema.gecos
    identity.homedir = schema.homedir
    identity.shell = schema.shell
    identity.credential = schema.credential
    await identity.save()
    return IdentityGetSchema.model_validate(identity)

@router.delete(path='/{uid}',
               summary='Remove an identity',
               description='Permanently remove an identity',
               response_description='There is no response content',
               responses={
                   204: {'model': None, 'description': 'The identity was removed'},
                   410: {'model': None, 'description': 'The identity was already gone'}
               })
async def identity_remove(uid: Annotated[UUID, fastapi.Path(description='The identity UUID')],
                           response: fastapi.Response):
    try:
        identity = await Identity.repository.get_by_uid(uid)
        await identity.remove()
        response.status_code = 204
    except EntityNotFoundException:
        response.status_code = 410
    return response
