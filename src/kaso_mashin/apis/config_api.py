import fastapi

from kaso_mashin import __version__
from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import Predefined_Images, ConfigSchema, ImagePredefinedSchema


class ConfigAPI(AbstractAPI):
    """
    The Config API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(tags=['config'])
        self._router.add_api_route('/', self.get_config, methods=['GET'],
                                   summary='Get Configuration',
                                   description='Get re-usable configuration to synchronise behaviour between the '
                                               'kaso-mashin client and server as well as reduce querying for otherwise '
                                               'static information.',
                                   response_description='Configuration data',
                                   status_code=200,
                                   response_model=ConfigSchema)

    async def get_config(self):
        return ConfigSchema(version=__version__,
                            predefined_images=[
                                ImagePredefinedSchema(name=k, url=v) for k, v in Predefined_Images.items()])
