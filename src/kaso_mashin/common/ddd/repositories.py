from .base_types import Repository
from .models import InstanceModel, ImageModel


class InstanceRepository(Repository[InstanceModel]):
    pass


class ImageRepository(Repository[ImageModel]):
    pass
