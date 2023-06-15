import typing
import pathlib
import sqlalchemy

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
        with self.db.session() as s:
            images = s.scalars(sqlalchemy.select(ImageModel)).all()
        return images

    def get(self, image_id: int) -> ImageModel:
        with self.db.session() as s:
            return s.get(ImageModel, image_id)

    def create(self, model: ImageModel) -> ImageModel:
        with self.db.session() as s:
            s.add(model)
            s.commit()
        return model

    def remove(self, image_id: int):
        with self.db.session() as s:
            image = s.get(ImageModel, image_id)
            s.delete(image)
            s.commit()
