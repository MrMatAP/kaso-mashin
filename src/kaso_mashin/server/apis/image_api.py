import typing
import uuid
import datetime
import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import (
    ExceptionSchema,
    Predefined_Images,
    ImagePredefinedSchema
)
from kaso_mashin.common.ddd_scaffold import EntityNotFoundException
from kaso_mashin.common.entities import (
    ImageEntity,
    ImageListSchema, ImageGetSchema, ImageCreateSchema, ImageModifySchema,
    TaskEntity,
    TaskGetSchema
)


class ImageAPI(AbstractAPI):
    """
    The Image API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._image_aggregate_root = None
        self._router = fastapi.APIRouter(tags=['images'],
                                         responses={
                                             404: {'model': ExceptionSchema, 'description': 'Image not found'},
                                             400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route(path='/predefined',
                                   endpoint=self.list_predefined_images,
                                   methods=['GET'],
                                   summary='List predefined images',
                                   description='List the currently predefined images you can download',
                                   response_description='A list of predefined images',
                                   status_code=200,
                                   responses={200: {'model': typing.List[ImagePredefinedSchema]}})

        self._router.add_api_route('/',
                                   endpoint=self.list_images,
                                   methods=['GET'],
                                   summary='List images',
                                   description='List all currently know images',
                                   response_description='The list of currently known images',
                                   status_code=200,
                                   responses={200: {'model': typing.List[ImageListSchema]}})
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.get_image,
                                   methods=['GET'],
                                   summary='Get an image',
                                   description='Get information about an image specified by its unique ID.',
                                   response_description='An image',
                                   status_code=200,
                                   response_model=ImageGetSchema)
        self._router.add_api_route(path='/',
                                   endpoint=self.create_image,
                                   methods=['POST'],
                                   summary='Create a new image',
                                   description='Creating an image is an asynchronous operation, you will get a task '
                                               'object back which you can subsequently check for progress using the '
                                               'task API',
                                   response_description='A task',
                                   status_code=201,
                                   response_model=TaskGetSchema)
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.modify_image,
                                   methods=['PUT'],
                                   summary='Modify an image',
                                   description='This will update the permissible fields of an image',
                                   response_description='The updated image',
                                   status_code=200,
                                   response_model=ImageGetSchema)
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.remove_image,
                                   methods=['DELETE'],
                                   summary='Remove an image',
                                   description='Remove the specified image. This will irrevocably and permanently '
                                               'delete the image and all disks that were created from it',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

    async def list_images(self):
        entities = await self._runtime.image_repository.list()
        return [ImageListSchema.model_validate(e) for e in entities]

    async def get_image(self,
                        uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                      description='The unique disk Id',
                                                                      examples=[
                                                                          '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._runtime.image_repository.get_by_uid(uid)
        return ImageGetSchema.model_validate(entity)

    async def create_image(self, schema: ImageCreateSchema, background_tasks: fastapi.BackgroundTasks):
        task = await TaskEntity.create(name=f'Download image {schema.name} from URL {schema.url}')
        now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
        imagepath = self._runtime.config.image_path / f'{schema.name}-{now}.qcow2'
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

    async def modify_image(self,
                           uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Image UUID',
                                                                         description='The unique image Id',
                                                                         examples=[
                                                                             '4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                           update: ImageModifySchema):
        entity = await self._runtime.image_repository.get_by_uid(uid)
        await entity.modify(min_vcpu=update.min_vcpu, min_ram=update.min_ram, min_disk=update.min_disk)
        return ImageGetSchema.model_validate(entity)

    async def remove_image(self,
                           uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Image UUID',
                                                                         description='The unique image Id',
                                                                         examples=[
                                                                             '4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                           response: fastapi.Response):
        try:
            entity = await self._runtime.image_repository.get_by_uid(uid)
            await entity.remove
            response.status_code = 204
        except EntityNotFoundException:
            response.status_code = 410
        return response

    async def list_predefined_images(self):
        predefined = [ImagePredefinedSchema(name=name, url=url) for name, url in Predefined_Images.items()]
        return predefined
