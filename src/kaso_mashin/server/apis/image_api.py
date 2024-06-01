import datetime
from typing import Annotated
from uuid import UUID

import fastapi

from kaso_mashin.common import AsyncRepository
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.entities import (
    ImageEntity,
    ImageListSchema,
    ImageGetSchema,
    ImageCreateSchema,
    ImageModifySchema,
    TaskEntity,
    TaskGetSchema,
)


class ImageAPI(
    BaseAPI[
        ImageListSchema,
        ImageGetSchema,
        ImageCreateSchema,
        ImageModifySchema,
    ]
):
    """
    The Image API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(
            runtime=runtime,
            name="Image",
            list_schema_type=ImageListSchema,
            get_schema_type=ImageGetSchema,
            create_schema_type=ImageCreateSchema,
            modify_schema_type=ImageModifySchema,
            async_create=True,
        )

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.image_repository

    async def create(
        self, schema: ImageCreateSchema, background_tasks: fastapi.BackgroundTasks
    ) -> TaskGetSchema:
        task = await TaskEntity.create(
            name=f"Download image {schema.name} from URL {schema.url}",
            msg="Downloading image",
        )
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
        imagepath = self._runtime.config.images_path / f"{schema.name}-{now}.qcow2"
        background_tasks.add_task(
            ImageEntity.create,
            task=task,
            user=self._runtime.owning_user,
            name=schema.name,
            url=schema.url,
            path=imagepath,
            min_vcpu=schema.min_vcpu,
            min_ram=schema.min_ram,
            min_disk=schema.min_disk,
        )
        return TaskGetSchema.model_validate(task)

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
        schema: ImageModifySchema,
        background_tasks: fastapi.BackgroundTasks,
    ) -> ImageGetSchema:
        entity: ImageEntity = await self._runtime.image_repository.get_by_uid(uid)
        await entity.modify(schema)
        return ImageGetSchema.model_validate(entity)
