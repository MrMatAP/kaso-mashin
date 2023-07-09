import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import TaskSchema, ImageSchema, ImageCreateSchema


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
                                   response_model=typing.Union[typing.List[ImageSchema], ImageSchema])
        self._router.add_api_route('/{image_id}', self.get_image,
                                   methods=['GET'],
                                   response_model=ImageSchema)
        self._router.add_api_route('/', self.create_image,
                                   methods=['PUT'],
                                   response_model=TaskSchema)
        self._router.add_api_route('/{image_id}', self.remove_image,
                                   methods=['DELETE'])

    async def list_images(self, name: typing.Optional[str] = None):
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

    async def get_image(self, image_id: int):
        """
        Return an image by its id
        Args:
            image_id: The image_id

        Returns:
            An ImageSchema
        """
        return self.image_controller.get(image_id=image_id)

    async def create_image(self, schema: ImageCreateSchema, background_tasks: fastapi.BackgroundTasks):
        task = self.task_controller.create(f'Download image {schema.name} from URL {schema.url}')
        background_tasks.add_task(self.image_controller.create, name=schema.name, url=schema.url, task=task)
        return task

    async def remove_image(self, image_id: int, response: fastapi.Response):
        gone = self.image_controller.remove(image_id)
        response.status_code = fastapi.status.HTTP_410_GONE if gone else fastapi.status.HTTP_204_NO_CONTENT
        return response
