from typing import Annotated
from uuid import UUID

import fastapi

from kaso_mashin.common import AsyncRepository
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.entities import (
    NetworkEntity,
    NetworkListSchema,
    NetworkListEntrySchema,
    NetworkGetSchema,
    NetworkCreateSchema,
    NetworkModifySchema,
)


class NetworkAPI(
    BaseAPI[
        NetworkListSchema,
        NetworkListEntrySchema,
        NetworkGetSchema,
        NetworkCreateSchema,
        NetworkModifySchema,
    ]
):
    """
    The Network API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(
            runtime=runtime,
            name="Network",
            list_schema_type=NetworkListSchema,
            list_entry_schema_type=NetworkListEntrySchema,
            get_schema_type=NetworkGetSchema,
            create_schema_type=NetworkCreateSchema,
            modify_schema_type=NetworkModifySchema,
        )

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.network_repository

    async def create(
        self, schema: NetworkCreateSchema, background_tasks: fastapi.BackgroundTasks
    ) -> NetworkGetSchema:
        entity: NetworkEntity = await NetworkEntity.create(
            name=schema.name, kind=schema.kind, cidr=schema.cidr, gateway=schema.gateway
        )
        return NetworkGetSchema.model_validate(entity)

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
        schema: NetworkModifySchema,
        background_tasks: fastapi.BackgroundTasks,
    ) -> NetworkGetSchema:
        entity = await self._runtime.network_repository.get_by_uid(uid)
        await entity.modify(name=schema.name, cidr=schema.cidr, gateway=schema.gateway)
        return NetworkGetSchema.model_validate(entity)
