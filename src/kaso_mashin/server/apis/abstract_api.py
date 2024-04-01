import abc
import logging
from typing import Generic, Type, Annotated, List
from uuid import UUID

import fastapi

from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common import (
    T_EntityListSchema, T_EntityGetSchema, T_EntityCreateSchema, T_EntityModifySchema,
    AsyncRepository, EntityNotFoundException
)
from kaso_mashin.common.entities import TaskGetSchema
from kaso_mashin.common.base_types import ExceptionSchema


class AbstractAPI(Generic[T_EntityListSchema, T_EntityGetSchema, T_EntityCreateSchema, T_EntityModifySchema], abc.ABC):
    """
    An abstract base class for APIs
    """

    def __init__(self,
                 runtime: Runtime,
                 name: str,
                 list_schema_type: Type[T_EntityListSchema],
                 get_schema_type: Type[T_EntityGetSchema],
                 create_schema_type: Type[T_EntityCreateSchema],
                 modify_schema_type: Type[T_EntityModifySchema]):
        self._runtime = runtime
        self._name = name
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
                                   summary=f'List {name} entities',
                                   description=f'List all currently known {name} entities',
                                   response_description=f'The list of known {name} entities',
                                   status_code=200,
                                   responses={200: {'model': list_schema_type}})
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.get,
                                   methods=['GET'],
                                   summary=f'Get a {name} entity by its UUID',
                                   description=f'Get all information for a {name} entity given its UUID',
                                   response_description=f'A {name} entity',
                                   status_code=200,
                                   response_model=get_schema_type)
        self._router.add_api_route(path='/',
                                   endpoint=self.create,
                                   methods=['POST'],
                                   summary=f'Create a {name} entity',
                                   description=f'Create a new {name} entity given the provided data',
                                   response_description=f'The created {name} entity',
                                   status_code=201,
                                   response_model=get_schema_type)
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.modify,
                                   methods=['PUT'],
                                   summary=f'Modify a {name} entity',
                                   description=f'Modify the allowed fields of a {name} entity given its UUID',
                                   response_description=f'The updated {name} entity',
                                   status_code=200,
                                   response_model=get_schema_type)
        self._router.add_api_route(path='/{uid}',
                                   endpoint=self.remove,
                                   methods=['DELETE'],
                                   summary=f'Remove a {name} entity',
                                   description=f'Permanently remove a {name} entity',
                                   response_description=f'There is no response content',
                                   responses={
                                       204: {'model': None, 'description': 'The entity was removed'},
                                       410: {'model': None, 'description': 'The entity was already gone'}})
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.info(f'Started API Router for {name}')

    async def list(self) -> List[T_EntityListSchema]:
        entities = await self.repository.list()
        return [self._list_schema_type.model_validate(e) for e in entities]

    async def get(self,
                  uid: Annotated[UUID, fastapi.Path(title='Entity UUID',
                                                    description='The UUID of the entity to get',
                                                    examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])]) -> T_EntityGetSchema:
        entity = await self.repository.get_by_uid(uid)
        return self._get_schema_type.model_validate(entity, strict=True)

    async def create(self,
                     schema: T_EntityCreateSchema,
                     background_tasks: fastapi.BackgroundTasks) -> T_EntityGetSchema | TaskGetSchema:
        """
        Create a new entity from data provided in request body
        Args:
            schema: The data to create the entity from
            background_tasks: Optional background_tasks for asynchronous updates

        Returns:
            A task
        """
        raise NotImplementedError

    async def modify(self,
                     uid: Annotated[UUID, fastapi.Path(title='Entity UUID',
                                                       description='The UUID of the entity to modify',
                                                       examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                     schema: T_EntityModifySchema,
                     background_tasks: fastapi.BackgroundTasks) -> T_EntityGetSchema:
        raise NotImplementedError

    async def remove(self,
                     uid: Annotated[UUID, fastapi.Path(title='Unique entity UUID',
                                                       description='The UUID of the entity to remove',
                                                       examples=['4198471B-8C84-4636-87CD-9DF4E24CF43F'])],
                     response: fastapi.Response):
        try:
            entity = await self.repository.get_by_uid(uid)
            await entity.remove()
            response.status_code = 204
        except EntityNotFoundException:
            response.status_code = 410
        return response

    @property
    @abc.abstractmethod
    def repository(self) -> AsyncRepository:
        raise NotImplementedError()

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def router(self) -> fastapi.APIRouter:
        return self._router
