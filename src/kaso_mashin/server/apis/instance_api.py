from typing import Annotated
from uuid import UUID

import fastapi

from kaso_mashin.common import (
    AsyncRepository,
    UniqueIdentifier,
    EntityNotFoundException,
)
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.base_types import ExceptionSchema
from kaso_mashin.common.entities import (
    InstanceEntity,
    InstanceListSchema,
    InstanceGetSchema,
    InstanceCreateSchema,
    InstanceModifySchema,
    TaskEntity,
    TaskGetSchema,
    ImageEntity,
    NetworkEntity,
    BootstrapEntity,
)


class InstanceAPI(
    BaseAPI[
        InstanceListSchema,
        InstanceGetSchema,
        InstanceCreateSchema,
        InstanceModifySchema,
    ]
):
    """
    The Instance API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(
            runtime=runtime,
            name="Instance",
            list_schema_type=InstanceListSchema,
            get_schema_type=InstanceGetSchema,
            create_schema_type=InstanceCreateSchema,
            modify_schema_type=InstanceModifySchema,
            async_create=True,
            async_modify=True,
        )

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.instance_repository

    async def create(
        self, schema: InstanceCreateSchema, background_tasks: fastapi.BackgroundTasks
    ) -> TaskGetSchema | ExceptionSchema:
        try:
            image: ImageEntity = await ImageEntity.repository.get_by_uid(
                UniqueIdentifier(schema.image_uid)
            )
            network: NetworkEntity = await NetworkEntity.repository.get_by_uid(
                UniqueIdentifier(schema.network_uid)
            )
            bootstrap: BootstrapEntity = await BootstrapEntity.repository.get_by_uid(
                UniqueIdentifier(schema.bootstrap_uid)
            )
            task = await TaskEntity.create(name=f"Creating instance {schema.name}")
            instance_path = self._runtime.config.instances_path / schema.name
            background_tasks.add_task(
                InstanceEntity.create,
                task=task,
                user=self._runtime.owning_user,
                name=schema.name,
                path=instance_path,
                uefi_code=self._runtime.uefi_code_path,
                uefi_vars=self._runtime.uefi_vars_path,
                vcpu=schema.vcpu,
                ram=schema.ram,
                image=image,
                os_disk_size=schema.os_disk_size,
                network=network,
                bootstrap=bootstrap,
            )
            return TaskGetSchema.model_validate(task)
        except EntityNotFoundException as e:
            return ExceptionSchema.model_validate(e)
        except Exception as e:
            return ExceptionSchema.model_validate(e)

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
        schema: InstanceModifySchema,
        background_tasks: fastapi.BackgroundTasks,
    ) -> TaskGetSchema:
        entity: InstanceEntity = await self._runtime.instance_repository.get_by_uid(uid)
        task = await TaskEntity.create(f"Modifying instance {entity.name}")
        background_tasks.add_task(entity.modify, schema=schema, task=task)
        return TaskGetSchema.model_validate(task)
