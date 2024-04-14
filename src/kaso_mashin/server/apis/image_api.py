import typing
import datetime
from typing import Annotated
from uuid import UUID

import fastapi
from pydantic import ValidationError

from kaso_mashin.common import AsyncRepository
from kaso_mashin.server.apis import BaseAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.config import Predefined_Images, ImagePredefinedSchema
from kaso_mashin.common.entities import (
    ImageEntity,
    ImageListSchema, ImageListEntrySchema, ImageGetSchema, ImageCreateSchema, ImageModifySchema,
    TaskEntity,
    TaskGetSchema
)


class ImageAPI(BaseAPI[ImageListSchema, ImageListEntrySchema, ImageGetSchema, ImageCreateSchema, ImageModifySchema]):
    """
    The Image API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime=runtime,
                         name='Image',
                         list_schema_type=ImageListSchema,
                         list_entry_schema_type=ImageListEntrySchema,
                         get_schema_type=ImageGetSchema,
                         create_schema_type=ImageCreateSchema,
                         modify_schema_type=ImageModifySchema,
                         async_create=True)

        self._router.add_api_route(path='/predefined',
                                   endpoint=self.list_predefined_images,
                                   methods=['GET'],
                                   summary='List predefined images',
                                   description='List the currently predefined images you can download',
                                   response_description='A list of predefined images',
                                   status_code=200,
                                   responses={200: {'model': typing.List[ImagePredefinedSchema]}})

    @property
    def repository(self) -> AsyncRepository:
        return self._runtime.image_repository

    async def create(self,
                     schema: ImageCreateSchema,
                     background_tasks: fastapi.BackgroundTasks) -> TaskGetSchema:
        task = await TaskEntity.create(name=f'Download image {schema.name} from URL {schema.url}',
                                       msg='Downloading image')
        now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
        imagepath = self._runtime.config.images_path / f'{schema.name}-{now}.qcow2'
        background_tasks.add_task(ImageEntity.create,
                                  task=task,
                                  user=self._runtime.owning_user,
                                  name=schema.name,
                                  url=schema.url,
                                  path=imagepath,
                                  min_vcpu=schema.min_vcpu,
                                  min_ram=schema.min_ram,
                                  min_disk=schema.min_disk)
        return TaskGetSchema.model_validate(task)

    async def modify(self, uid: Annotated[UUID, fastapi.Path(title='Entity UUID',
                                                             description='The UUID of the entity to modify',
                                                             examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                     schema: ImageModifySchema,
                     background_tasks: fastapi.BackgroundTasks) -> ImageGetSchema:
        entity: ImageEntity = await self._runtime.image_repository.get_by_uid(uid)
        await entity.modify(min_vcpu=schema.min_vcpu,
                            min_ram=schema.min_ram,
                            min_disk=schema.min_disk)
        return ImageGetSchema.model_validate(entity)

    async def list_predefined_images(self):
        predefined = [ImagePredefinedSchema(name=name, url=url) for name, url in Predefined_Images.items()]
        return predefined
