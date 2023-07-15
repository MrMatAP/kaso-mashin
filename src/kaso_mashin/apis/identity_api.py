import typing
import fastapi

from kaso_mashin.apis import AbstractAPI
from kaso_mashin.runtime import Runtime
from kaso_mashin.model import ExceptionSchema, IdentitySchema, IdentityCreateSchema


class IdentityAPI(AbstractAPI):
    """
    The identity API
    """

    def __init__(self, runtime: Runtime):
        super().__init__(runtime)
        self._router = fastapi.APIRouter(
            tags=['identities'],
            responses={
                fastapi.status.HTTP_404_NOT_FOUND: {'model': ExceptionSchema, 'description': 'Image not found'},
                fastapi.status.HTTP_400_BAD_REQUEST: {'model': ExceptionSchema, 'description': 'Incorrect input'}})
        self._router.add_api_route('/', self.list_identities,
                                   methods=['GET'],
                                   summary='List known identities',
                                   description='List all known identities. You can optionally filter the list by the'
                                               '"name" query parameter',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {
                                           'model': typing.Union[typing.List[IdentitySchema], IdentitySchema]}
                                   })
        self._router.add_api_route('/{identity_id}', self.get_identity,
                                   methods=['GET'],
                                   summary='Get an identity by its unique id',
                                   description='Get full information about an identity specified by its unique id',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {'model': IdentitySchema}
                                   })
        self._router.add_api_route('/', self.create_identity,
                                   methods=['POST'],
                                   summary='Create an identity',
                                   description='Create an identity',
                                   responses={
                                       fastapi.status.HTTP_201_CREATED: {'model': IdentitySchema}
                                   })
        self._router.add_api_route('/{identity_id}', self.modify_identity,
                                   methods=['PUT'],
                                   summary='Modify an identity',
                                   description='Modify an identity',
                                   responses={
                                       fastapi.status.HTTP_200_OK: {'model': IdentitySchema}
                                   })
        self._router.add_api_route('/{identity_id}', self.remove_identity,
                                   methods=['DELETE'],
                                   summary='Remove an identity',
                                   description='Remove an identity',
                                   responses={
                                       fastapi.status.HTTP_204_NO_CONTENT: {'model': None},
                                       fastapi.status.HTTP_410_GONE: {'model': None}})

    async def list_identities(self,
                              name: typing.Annotated[str | None, fastapi.Query(description='The identity name')] = None):
        """
        List all known images
        """
        if name:
            return self.identity_controller.get(name=name)
        return self.identity_controller.list()

    async def get_identity(self,
                           identity_id: typing.Annotated[int, fastapi.Path(description='The unique identity id')]):
        """
        Return an identity by its id
        """
        identity = self.identity_controller.get(identity_id=identity_id)
        return identity or fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_404_NOT_FOUND,
                                                       content=ExceptionSchema(status=fastapi.status.HTTP_404_NOT_FOUND,
                                                                               msg='No such identity could be found')
                                                       .model_dump())

    async def create_identity(self, schema: IdentityCreateSchema):
        return fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                              content=ExceptionSchema(status=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                                                      msg='Not yet implemented').model_dump())

    async def modify_identity(self,
                              identity_id: typing.Annotated[int, fastapi.Path(description='The unique identity id')],
                              schema: IdentitySchema):
        return fastapi.responses.JSONResponse(status_code=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                              content=ExceptionSchema(status=fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                                                                      msg='Not yet implemented').model_dump())

    async def remove_identity(self,
                              identity_id: typing.Annotated[int, fastapi.Path(description='The unique identity id')],
                              response: fastapi.Response):
        gone = self.identity_controller.remove(identity_id)
        response.status_code = fastapi.status.HTTP_410_GONE if gone else fastapi.status.HTTP_204_NO_CONTENT
        return response
