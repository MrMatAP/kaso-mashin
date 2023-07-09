import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import ExceptionSchema, TaskSchema, ImageSchema, ImageCreateSchema


class ImageAPI(AbstractAPI):
    """
    The Image API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['images'],
            responses={404: {'description': 'Image not found'}})
        self._router.add_api_route('/', self.list_images,
                                   methods=['GET'],
                                   summary='List known images',
                                   description='List all known images. You can filter the list by image name using the '
                                               'optional "name" query parameter',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {'model': typing.Union[typing.List[ImageSchema], ImageSchema]},
                                       fastapi.status.HTTP_400_BAD_REQUEST: {'model': ExceptionSchema}
                                   })
        self._router.add_api_route('/{image_id}', self.get_image,
                                   methods=['GET'],
                                   summary='Get an image by its unique id',
                                   description='Get information about an image specified by its unique id',
                                   responses={
                                       fastapi.status.HTTP_404_NOT_FOUND: {'model': ExceptionSchema},
                                       fastapi.status.HTTP_400_BAD_REQUEST: {'model': ExceptionSchema},
                                       fastapi.status.HTTP_200_OK: {'model': ImageSchema}
                                   })
        self._router.add_api_route('/', self.create_image,
                                   methods=['PUT'],
                                   summary='Create an image',
                                   description='Creating an image is an asynchronous operation, you will get a task '
                                               'object back which you can subsequently check for progress using the '
                                               'task API',
                                   responses={
                                       fastapi.status.HTTP_400_BAD_REQUEST: {'model': ExceptionSchema},
                                       fastapi.status.HTTP_200_OK: {'model': TaskSchema}
                                   })
        self._router.add_api_route('/{image_id}', self.remove_image,
                                   methods=['DELETE'],
                                   summary='Remove an image',
                                   description='Remove an image specified by its unique id',
                                   responses={
                                       fastapi.status.HTTP_204_NO_CONTENT: {'model': None},
                                       fastapi.status.HTTP_410_GONE: {'model': None}
                                   })

    async def list_images(self,
                          name: typing.Annotated[str | None,
                                                 fastapi.Query(description='The image name')] = None):
        """
        List images or, if the 'name' query parameter is provided then get an image by its name
        Args:
            name: The optional image name query parameter

        Returns:
            If no image name was provided then a list of ImageSchema, otherwise the ImageSchema
            for the single image found
        """
        if name:
            return self.image_controller.get(name=name)
        return self.image_controller.list()

    async def get_image(self,
                        image_id: typing.Annotated[int, fastapi.Path(description='The unique image id')]):
        """
        Return an image by its id
        Args:
            image_id: The image_id

        Returns:
            An ImageSchema
        """
        image = self.image_controller.get(image_id=image_id)
        return image or fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_404_NOT_FOUND,
                                                       content=ExceptionSchema(status=fastapi.status.HTTP_404_NOT_FOUND,
                                                                               msg='No such image could be found')
                                                       .model_dump())

    async def create_image(self, schema: ImageCreateSchema, background_tasks: fastapi.BackgroundTasks):
        task = self.task_controller.create(f'Download image {schema.name} from URL {schema.url}')
        background_tasks.add_task(self.image_controller.create, name=schema.name, url=schema.url, task=task)
        return task

    async def remove_image(self,
                           image_id: typing.Annotated[int, fastapi.Path(description='The unique image id')],
                           response: fastapi.Response):
        gone = self.image_controller.remove(image_id)
        response.status_code = fastapi.status.HTTP_410_GONE if gone else fastapi.status.HTTP_204_NO_CONTENT
        return response
