import typing
import sqlalchemy

from kaso_mashin import KasoMashinException
from kaso_mashin.config import Config
from kaso_mashin.controllers import AbstractController
from kaso_mashin.db import DB
from kaso_mashin.model import ImageModel


class ImageController(AbstractController):
    """
    An image controller
    """

    def __init__(self, config: Config, db: DB):
        super().__init__(config, db)
        config.path.joinpath('images').mkdir(parents=True, exist_ok=True)

    def list(self) -> typing.List[ImageModel]:
        images = self.db.session.scalars(sqlalchemy.select(ImageModel)).all()
        return images

    def get(self, image_id: typing.Optional[int] = None, name: typing.Optional[str] = None) -> ImageModel | None:
        """
        Return a Image by either id or name
        Args:
            image_id: The image id
            name: The network name

        Returns:
            The ImageModel matching the search parameters
        Raises:
            KasoMashinException: When neither image_id nor name is specified
        """
        if not image_id and not name:
            raise KasoMashinException(status=400, msg='Neither image_id nor name are provided')
        if image_id:
            return self.db.session.get(ImageModel, image_id)
        return self.db.session.scalar(
            sqlalchemy.sql.select(ImageModel).where(ImageModel.name == name))

    def create(self, model: ImageModel) -> ImageModel:
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def remove(self, image_id: int):
        image = self.db.session.get(ImageModel, image_id)
        self.db.session.delete(image)
        self.db.session.commit()
