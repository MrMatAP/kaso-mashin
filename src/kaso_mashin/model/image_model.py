from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
import pydantic

from kaso_mashin import Base
from kaso_mashin.custom_types import DbPath, SchemaPath


class ImageSchema(pydantic.BaseModel):
    """
    An Image
    """
    model_config = pydantic.ConfigDict(from_attributes=True)

    image_id: int = pydantic.Field(description='The image id', examples=[1])
    name: str = pydantic.Field(description='The image name', examples=['jammy'])
    path: SchemaPath = pydantic.Field(description='Path to the image on the local disk',
                                      examples=['/Users/dude/var/kaso/images/ubuntu-jammy.qcow2'])
    min_cpu: int = pydantic.Field(description='Minimum number of vCPUs',
                                  default=0,
                                  examples=[2])
    min_ram: int = pydantic.Field(description='Minimum number of RAM (in MB)',
                                  default=0,
                                  examples=[2048])
    min_space: int = pydantic.Field(description='Minimum number of disk space (in MB)',
                                    default=0,
                                    examples=[10000])


class ImageCreateSchema(pydantic.BaseModel):
    """
    An input schema to create an image
    """
    name: str = pydantic.Field(description='The image name',
                               examples=['jammy'])
    url: str = pydantic.Field(description='The source URL from where to download the image from. This may be over HTTP '
                                          'or from a file URL.',
                              examples=['https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img'])
    min_cpu: int = pydantic.Field(description='Minimum number of vCPUs',
                                  default=0,
                                  examples=[2])
    min_ram: int = pydantic.Field(description='Minimum number of RAM (in MB)',
                                  default=0,
                                  examples=[2048])
    min_space: int = pydantic.Field(description='Minimum number of disk space (in MB)',
                                    default=0,
                                    examples=[10000])


class ImageModifySchema(pydantic.BaseModel):
    """
    Input schema for modifying an image
    """
    min_cpu: int = pydantic.Field(description='Minimum number of vCPUs',
                                  default=0,
                                  examples=[2])
    min_ram: int = pydantic.Field(description='Minimum number of RAM (in MB)',
                                  default=0,
                                  examples=[2048])
    min_space: int = pydantic.Field(description='Minimum number of disk space (in MB)',
                                    default=0,
                                    examples=[10000])


class ImageModel(Base):
    """
    Representation of an image in the database
    """

    __tablename__ = 'images'
    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    path: Mapped[str] = mapped_column(DbPath, unique=True)

    min_cpu: Mapped[int] = mapped_column(Integer, default=0)
    min_ram: Mapped[int] = mapped_column(Integer, default=0)
    min_space: Mapped[int] = mapped_column(Integer, default=0)

    @staticmethod
    def from_schema(schema: ImageCreateSchema | ImageModifySchema) -> 'ImageModel':
        model = ImageModel(
            min_cpu=schema.min_cpu,
            min_ram=schema.min_ram,
            min_space=schema.min_space)
        if isinstance(schema, ImageCreateSchema):
            model.name = schema.name
        return model

    def __eq__(self, other) -> bool:
        return all([
            isinstance(other, ImageModel),
            self.image_id == other.image_id,
            self.name == other.name,
            self.path == other.path,
            self.min_cpu == other.min_cpu,
            self.min_ram == other.min_ram,
            self.min_space == other.min_space])

    def __repr__(self) -> str:
        return f'ImageModel(' \
               f'image_id={self.image_id}, ' \
               f'name="{self.name}", ' \
               f'path="{self.path}, ' \
               f'min_cpu={self.min_cpu}, ' \
               f'min_ram={self.min_ram}, ' \
               f'min_space={self.min_space})'
