import typing
import uuid
import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import (
    ExceptionSchema, TaskSchema,
    Predefined_Images,
    ImagePredefinedSchema
)
from kaso_mashin.common.base_types import EntityNotFoundException
from kaso_mashin.common.entities import (
    ImageAggregateRoot, ImageEntity, ImageModel,
    ImageListSchema, ImageGetSchema, ImageCreateSchema, ImageModifySchema
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
                                   responses={200: {'model': typing.List[ImageListSchema]}},
                                   dependencies=[fastapi.Depends(self.image_aggregate_root)])
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.get_image,
                                   methods=['GET'],
                                   summary='Get an image',
                                   description='Get information about an image specified by its unique ID.',
                                   response_description='An image',
                                   status_code=200,
                                   response_model=ImageGetSchema,
                                   dependencies=[fastapi.Depends(self.image_aggregate_root)])
        self._router.add_api_route(path='/',
                                   endpoint=self.create_image,
                                   methods=['POST'],
                                   summary='Create a new image',
                                   description='Creating an image is an asynchronous operation, you will get a task '
                                               'object back which you can subsequently check for progress using the '
                                               'task API',
                                   response_description='A task',
                                   status_code=201,
                                   response_model=TaskSchema,
                                   dependencies=[fastapi.Depends(self.image_aggregate_root)])
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.modify_image,
                                   methods=['PUT'],
                                   summary='Modify an image',
                                   description='This will update the permissible fields of an image',
                                   response_description='The updated image',
                                   status_code=200,
                                   response_model=ImageGetSchema,
                                   dependencies=[fastapi.Depends(self.image_aggregate_root)])
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.remove_image,
                                   methods=['DELETE'],
                                   summary='Remove an image',
                                   description='Remove the specified image. This will irrevocably and permanently '
                                               'delete the image and all disks that were created from it',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}},
                                   dependencies=[fastapi.Depends(self.image_aggregate_root)])

    async def image_aggregate_root(self) -> ImageAggregateRoot:
        if self._image_aggregate_root is None:
            self._image_aggregate_root = ImageAggregateRoot(model=ImageModel,
                                                            session_maker=await self._runtime.db.async_sessionmaker)
        return self._image_aggregate_root

    async def list_images(self):
        entities = await self._image_aggregate_root.list(force_reload=True)
        return [ImageListSchema.model_validate(e) for e in entities]

    async def get_image(self,
                        uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Disk UUID',
                                                                      description='The unique disk Id',
                                                                      examples=[
                                                                          '4198471B-8C84-4636-87CD-9DF4E24CF43F'])]):
        entity = await self._image_aggregate_root.get(uid)
        return ImageGetSchema.model_validate(entity)

    async def create_image(self, schema: ImageCreateSchema, background_tasks: fastapi.BackgroundTasks):
        task = self.task_controller.create(name=f'Download image {schema.name} from URL {schema.url}')
        background_tasks.add_task(self.image_controller.create,
                                  name=schema.name,
                                  url=schema.url,
                                  min_cpu=schema.min_cpu,
                                  min_ram=schema.min_ram,
                                  min_space=schema.min_space,
                                  task=task)
        return task

    async def modify_image(self,
                           uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Image UUID',
                                                                         description='The unique image Id',
                                                                         examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                           update: ImageModifySchema):
        entity = await self._image_aggregate_root().get(uid)
        entity.min_cpu = update.min_cpu
        entity.min_ram = update.min_ram
        entity.min_disk = update.min_disk
        return ImageGetSchema.model_validate(entity)

    async def remove_image(self,
                           uid: typing.Annotated[uuid.UUID, fastapi.Path(title='Image UUID',
                                                                         description='The unique image Id',
                                                                         examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                           response: fastapi.Response):
        try:
            entity = await self._image_aggregate_root.get(uid)
            await entity.remove
            response.status_code = 204
        except EntityNotFoundException:
            response.status_code = 410
        return response

    async def list_predefined_images(self):
        predefined = [ImagePredefinedSchema(name=name, url=url) for name, url in Predefined_Images.items()]
        return predefined
