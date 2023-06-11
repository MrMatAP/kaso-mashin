from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import Base


class ImageModel(Base):
    """
    Representation of an image in the database
    """

    __tablename__ = 'images'
    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    path: Mapped[str] = mapped_column(String, unique=True)
