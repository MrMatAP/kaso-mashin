from typing import Annotated
from uuid import UUID

import fastapi

from kaso_mashin.common import AsyncRepository
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.entities import (
    BootstrapEntity,
    BootstrapListSchema,
    BootstrapListEntrySchema,
    BootstrapGetSchema,
    BootstrapCreateSchema,
    BootstrapModifySchema,
)


class BootstrapAPI(
    BaseAPI[
        BootstrapListSchema,
        BootstrapListEntrySchema,
        BootstrapGetSchema,
        BootstrapCreateSchema,
        BootstrapModifySchema,
    ]
):
    """
    The Bootstrap API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(
            runtime=runtime,
            name="Bootstrap Template",
            list_schema_type=BootstrapListSchema,
            list_entry_schema_type=BootstrapListEntrySchema,
            get_schema_type=BootstrapGetSchema,
            create_schema_type=BootstrapCreateSchema,
            modify_schema_type=BootstrapModifySchema,
        )

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.bootstrap_repository

    async def create(
        self, schema: BootstrapCreateSchema, background_tasks: fastapi.BackgroundTasks
    ) -> BootstrapGetSchema:
        entity = await BootstrapEntity.create(
            name=schema.name, kind=schema.kind, content=schema.content
        )
        return BootstrapGetSchema.model_validate(entity)

    async def modify(
        self,
        uid: Annotated[
            UUID,
            fastapi.Path(
                title="Entity UUID",
                description="The UUID of the entity to modify",
                examples=["4198471B-8C84-4636-87CD-9DF4E24CF43F"],
            ),
        ],
        schema: BootstrapModifySchema,
        background_tasks: fastapi.BackgroundTasks,
    ) -> BootstrapGetSchema:
        entity: BootstrapEntity = await self.repository.get_by_uid(uid)
        await entity.modify(name=schema.name, kind=schema.kind, content=schema.content)
        return BootstrapGetSchema.model_validate(entity)
