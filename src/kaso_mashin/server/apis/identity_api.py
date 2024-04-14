from typing import Annotated
import pathlib
from uuid import UUID

import fastapi

from kaso_mashin.common import AsyncRepository
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.entities import (
    IdentityEntity,
    IdentityListSchema, IdentityListEntrySchema, IdentityGetSchema, IdentityCreateSchema, IdentityModifySchema,
    TaskGetSchema
)


class IdentityAPI(BaseAPI[IdentityListSchema, IdentityListEntrySchema, IdentityGetSchema, IdentityCreateSchema, IdentityModifySchema]):
    """
    The identity API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime,
                         name='Identity',
                         list_schema_type=IdentityListSchema,
                         list_entry_schema_type=IdentityListEntrySchema,
                         get_schema_type=IdentityGetSchema,
                         create_schema_type=IdentityCreateSchema,
                         modify_schema_type=IdentityModifySchema)

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.identity_repository

    async def create(self, schema: IdentityCreateSchema,
                     background_tasks: fastapi.BackgroundTasks) -> IdentityGetSchema | TaskGetSchema:
        entity = await IdentityEntity.create(name=schema.name,
                                             kind=schema.kind,
                                             gecos=schema.gecos,
                                             homedir=pathlib.Path(schema.homedir),
                                             shell=schema.shell,
                                             credential=schema.credential)
        return IdentityGetSchema.model_validate(entity)

    async def modify(self, uid: Annotated[UUID, fastapi.Path(title='Entity UUID',
                                                             description='The UUID of the entity to modify',
                                                             examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                     schema: IdentityModifySchema, background_tasks: fastapi.BackgroundTasks) -> IdentityGetSchema:
        entity: IdentityEntity = await self.repository.get_by_uid(uid)
        await entity.modify(schema)
        return IdentityGetSchema.model_validate(entity)
