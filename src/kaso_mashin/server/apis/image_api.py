import typing
import fastapi

from kaso_mashin.server.apis import AbstractAPI
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import (
    ExceptionSchema, TaskSchema,
    Predefined_Images,
    ImageModel, ImageSchema, ImageCreateSchema, ImageModifySchema, ImagePredefinedSchema)


class ImageAPI(AbstractAPI):
    """
    The Image API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['images'],
            responses={
                404: {'model': ExceptionSchema, 'description': 'Image not found'},
                400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route('/predefined', self.list_predefined_images, methods=['GET'],
                                   summary='List predefined images',
                                   description='List the currently predefined images you can download',
                                   response_description='A list of predefined images',
                                   status_code=200,
                                   responses={200: {'model': typing.List[ImagePredefinedSchema]}})
        self._router.add_api_route('/', self.list_images, methods=['GET'],
                                   summary='List images',
                                   description='List all known images. You can optionally filter the list by the'
                                               '"name" query parameter. If you do filter using the "name" query '
                                               'parameter then the corresponding single image is returned.',
                                   response_description='A list of images, or a single identity when filtered by name',
                                   status_code=200,
                                   responses={200: {'model': typing.Union[typing.List[ImageSchema], ImageSchema]}})
        self._router.add_api_route('/{image_id}', self.get_image, methods=['GET'],
                                   summary='Get an image',
                                   description='Get full information about an image specified by its unique ID.',
                                   response_description='An image',
                                   status_code=200,
                                   response_model=ImageSchema)
        self._router.add_api_route('/', self.create_image, methods=['POST'],
                                   summary='Create a image',
                                   description='Creating an image is an asynchronous operation, you will get a task '
                                               'object back which you can subsequently check for progress using the '
                                               'task API',
                                   response_description='A task',
                                   status_code=201,
                                   response_model=TaskSchema)
        self._router.add_api_route('/{image_id}', self.modify_image, methods=['PUT'],
                                   summary='Modify a image',
                                   description='This will update the permissible fields of an image based on the '
                                               'provided input.',
                                   response_description='The updated image',
                                   status_code=200,
                                   response_model=ImageSchema)
        self._router.add_api_route('/{image_id}', self.remove_image, methods=['DELETE'],
                                   summary='Remove an image',
                                   description='Remove the specified image. This will irrevocably and permanently '
                                               'delete the image.',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

    async def list_images(self,
                          name: typing.Annotated[str | None, fastapi.Query(title='Image name',
                                                                           description='A unique image name',
                                                                           examples=['jammy'])] = None):
        if name:
            return self.image_controller.get(name=name)
        return self.image_controller.list()

    async def get_image(self,
                        image_id: typing.Annotated[int, fastapi.Path(title='Image ID',
                                                                     description='A unique image id',
                                                                     examples=[1])]):
        image = self.image_controller.get(image_id=image_id)
        return image or fastapi.responses.JSONResponse(status_code=404,
                                                       content=ExceptionSchema(status=404,
                                                                               msg='No such image could be found')
                                                       .model_dump())

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
                           image_id: typing.Annotated[int, fastapi.Path(title='Image ID',
                                                                        description='The image ID to modify',
                                                                        examples=[1])],
                           schema: ImageModifySchema):
        return self.image_controller.modify(image_id=image_id,
                                            update=ImageModel.from_schema(schema))

    async def remove_image(self,
                           image_id: typing.Annotated[int, fastapi.Path(title='Image ID',
                                                                        description='The image ID to remove',
                                                                        examples=[1])],
                           response: fastapi.Response):
        gone = self.image_controller.remove(image_id)
        response.status_code = 410 if gone else 204
        return response

    async def list_predefined_images(self):
        predefined = [ImagePredefinedSchema(name=name, url=url) for name, url in Predefined_Images.items()]
        return predefined
