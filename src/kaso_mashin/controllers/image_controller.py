import typing
import sqlalchemy
import httpx
import aiofiles

from kaso_mashin import KasoMashinException
from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import ImageModel, TaskSchema


class ImageController(AbstractController):
    """
    An image controller
    """

    def __init__(self, runtime: 'Runtime'):
        super().__init__(runtime)
        self.config.path.joinpath('images').mkdir(parents=True, exist_ok=True)

    def list(self) -> typing.List[ImageModel]:
        images = list(self.db.session.scalars(sqlalchemy.select(ImageModel)).all())
        return images

    def get(self, image_id: int | None = None, name: str | None = None) -> ImageModel | None:
        """
        Return an existing image by either its id or name
        Args:
            image_id: An optional image id
            name: An optional network name

        Returns:
            The ImageModel matching the search parameters
        Raises:
            KasoMashinException: When neither image_id nor name is specified
        """
        if not image_id and not name:
            raise KasoMashinException(status=400, msg='Neither image_id nor name are provided')
        if image_id:
            image = self.db.session.get(ImageModel, image_id)
        else:
            image = self.db.session.scalar(sqlalchemy.sql.select(ImageModel).where(ImageModel.name == name))
        return image or None

    async def create(self, name: str, url: str, task: TaskSchema) -> ImageModel:
        image_path = self.config.path.joinpath(f'images/{name}.qcow2')
        if image_path.exists():
            raise KasoMashinException(status=400,
                                      msg=f'Image at path {image_path} already exists',
                                      task=task)

        resp = httpx.head(url, follow_redirects=True, timeout=60)
        size = int(resp.headers.get('content-length'))
        current = 0
        client = httpx.AsyncClient(follow_redirects=True, timeout=60)
        async with client.stream('GET', url) as resp, aiofiles.open(image_path, 'wb') as i:
            async for chunk in resp.aiter_bytes():
                await i.write(chunk)
                current += 8192
                task.progress(percent_complete=int(current / size * 100), msg='Downloading')
        model = ImageModel(name=name, path=image_path)
        self.db.session.add(model)
        self.db.session.commit()
        task.success(f'Downloaded to image with id {model.image_id}')
        return model

    def modify(self, image_id: int, update: ImageModel) -> ImageModel:
        current = self.db.session.get(ImageModel, image_id)
        if not current:
            raise KasoMashinException(status=404, msg='The image could not be found')
        if update.min_cpu > -1:
            current.min_cpu = update.min_cpu
        if update.min_ram > -1:
            current.min_ram = update.min_ram
        if update.min_space > -1:
            current.min_space = update.min_space
        self.db.session.add(current)
        self.db.session.commit()
        return current

    def remove(self, image_id: int) -> bool:
        """
        Remove an image
        Args:
            image_id: The image id to remove

        Returns:
            False if the image was actually removed as part of this call, True if it was already gone or didn't exist
            in the first place
        """
        # TODO: Should check whether it's in use somewhere
        image = self.db.session.get(ImageModel, image_id)
        if not image:
            # The image is not around, should cause a 410
            return True
        image.path.unlink(missing_ok=True)
        self.db.session.delete(image)
        self.db.session.commit()
        return False
