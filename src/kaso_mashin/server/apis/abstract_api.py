import abc
import logging
import fastapi

from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common import EntitySchema, AsyncRepository
from kaso_mashin.common.model import ExceptionSchema


class AbstractAPI(abc.ABC):
    """
    An abstract base class for APIs
    """

    def __init__(self,
                 runtime: Runtime,
                 name: str,
                 repository: AsyncRepository,
                 list_schema_type: EntitySchema,
                 get_schema_type: EntitySchema,
                 create_schema_type: EntitySchema,
                 modify_schema_type: EntitySchema):
        self._runtime = runtime
        self._name = name
        self._repository = repository
        self._list_schema_type = list_schema_type
        self._get_schema_type = get_schema_type
        self._create_schema_type = create_schema_type
        self._modify_schema_type = modify_schema_type
        self._router = fastapi.APIRouter(tags=[name],
                                         responses={
                                             404: {'model': ExceptionSchema, 'description': f'{name} entity not found'},
                                             400: {'model': ExceptionSchema, 'description': 'Bad input'}})
        self._router.add_api_route(path='/',
                                   endpoint=self.list,
                                   methods=['GET'],
                                   summary=f'List {name}',
                                   description=f'List all currently known {name} entities',
                                   response_description=f'The list of known {name} entities',
                                   status_code=200,
                                   responses={200: {'model': list_schema_type}})
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.info(f'Started API Router for {name}')

    async def list(self):
        entities = await self._repository.list()
        return [list_schema_type.model_validate(e) for e in entities]

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def router(self) -> fastapi.APIRouter:
        return self._router
