import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import ExceptionSchema, IdentitySchema, IdentityCreateSchema, IdentityModifySchema, IdentityModel


class IdentityAPI(AbstractAPI):
    """
    The identity API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(tags=['identities'],
                                         responses={
                                             404: {'model': ExceptionSchema, 'description': 'Identity not found'},
                                             400: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route('/', self.list_identities, methods=['GET'],
                                   summary='List identities',
                                   description='List all known identities. You can optionally filter the list by the'
                                               '"name" query parameter. If you do filter using the "name" query '
                                               'parameter then the corresponding single identity is returned.',
                                   response_description='A list of identities, or a single identity when filtered by '
                                                        'name',
                                   status_code=200,
                                   responses={
                                       200: {'model': typing.Union[typing.List[IdentitySchema], IdentitySchema]}
                                   })
        self._router.add_api_route('/{identity_id}', self.get_identity, methods=['GET'],
                                   summary='Get an identity',
                                   description='Get full information about an identity specified by its unique ID.',
                                   response_description='An identity',
                                   status_code=200,
                                   response_model=IdentitySchema)
        self._router.add_api_route('/', self.create_identity, methods=['POST'],
                                   summary='Create an identity',
                                   description='This will create an identity based on the provided input.',
                                   response_description='The created identity',
                                   status_code=201,
                                   response_model=IdentitySchema)
        self._router.add_api_route('/{identity_id}', self.modify_identity, methods=['PUT'],
                                   summary='Modify an identity',
                                   description='This will update the permissible fields of an identity based on the '
                                               'provided input. Neither name, kind or identity_id may be modified.',
                                   response_description='The updated identity',
                                   status_code=200,
                                   response_model=IdentitySchema)
        self._router.add_api_route('/{identity_id}', self.remove_identity, methods=['DELETE'],
                                   summary='Remove an identity',
                                   description='Remove an identity. This will irrevocably and permanently delete the '
                                               'identity.',
                                   response_description='There is no response content',
                                   responses={204: {'model': None}, 410: {'model': None}})

    async def list_identities(self,
                              name: typing.Annotated[str | None,
                                                     fastapi.Query(title='Identity name',
                                                                   description='A unique identity name',
                                                                   examples=['mrmat'])] = None):
        if name:
            return self.identity_controller.get(name=name)
        return self.identity_controller.list()

    async def get_identity(self,
                           identity_id: typing.Annotated[int, fastapi.Path(title='Identity ID',
                                                                           description='A unique identity ID',
                                                                           examples=[1])]):
        identity = self.identity_controller.get(identity_id=identity_id)
        return identity or fastapi.responses.JSONResponse(status_code=404,
                                                          content=ExceptionSchema(status=404,
                                                                                  msg='No such identity could be found')
                                                          .model_dump())

    async def create_identity(self, schema: IdentityCreateSchema):
        model = self.identity_controller.create(IdentityModel.from_schema(schema))
        return model

    async def modify_identity(self,
                              identity_id: typing.Annotated[int, fastapi.Path(title='Identity ID',
                                                                              description='The unique identity ID',
                                                                              examples=[1])],
                              schema: IdentityModifySchema):
        return self.identity_controller.modify(identity_id=identity_id, update=IdentityModel.from_schema(schema))

    async def remove_identity(self,
                              identity_id: typing.Annotated[int, fastapi.Path(title='Identity ID',
                                                                              description='The unique identity ID',
                                                                              examples=[1])],
                              response: fastapi.Response):
        gone = self.identity_controller.remove(identity_id)
        response.status_code = 410 if gone else 204
        return response
