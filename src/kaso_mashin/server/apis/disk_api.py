from typing import Annotated
from uuid import UUID
import pathlib

import fastapi

from kaso_mashin.common import AsyncRepository
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.entities import (
    DiskEntity,
    DiskListSchema, DiskListEntrySchema, DiskGetSchema, DiskCreateSchema, DiskModifySchema
)


class DiskAPI(BaseAPI[DiskListSchema, DiskListEntrySchema, DiskGetSchema, DiskCreateSchema, DiskModifySchema]):
    """
    The Disk API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime=runtime,
                         name='Disk',
                         list_schema_type=DiskListSchema,
                         list_entry_schema_type=DiskListEntrySchema,
                         get_schema_type=DiskGetSchema,
                         create_schema_type=DiskCreateSchema,
                         modify_schema_type=DiskModifySchema)

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.disk_repository

    async def create(self,
                     schema: DiskCreateSchema,
                     background_tasks: fastapi.BackgroundTasks) -> DiskGetSchema:
        image = None
        if schema.image_uid is not None:
            image = await self.repository.get_by_uid(schema.image_uid)
        entity = await DiskEntity.create(name=schema.name,
                                         path=pathlib.Path(schema.path),
                                         size=schema.size,
                                         disk_format=schema.disk_format,
                                         image=image)
        return DiskGetSchema.model_validate(entity)

    async def modify(self,
                     uid: Annotated[UUID, fastapi.Path(title='Entity UUID',
                                                             description='The UUID of the entity to modify',
                                                             examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                     schema: DiskModifySchema,
                     background_tasks: fastapi.BackgroundTasks) -> DiskGetSchema:
        entity = await self.repository.get_by_uid(uid)
        if entity.size != schema.size:
            entity = await entity.resize(schema.size)
        return DiskGetSchema.model_validate(entity)
