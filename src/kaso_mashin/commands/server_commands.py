import argparse

import fastapi
import uvicorn

from kaso_mashin import __version__, KasoMashinException
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.apis import ConfigAPI, TaskAPI, ImageAPI, IdentityAPI, NetworkAPI, InstanceAPI


class ServerCommands(AbstractCommands):
    """
    Implementation of the server command (group)
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        parser.add_argument('--host',
                            dest='host',
                            type=str,
                            required=False,
                            default=self.config.default_server_host,
                            help='The host to bind to')
        parser.add_argument('--port',
                            dest='port',
                            type=int,
                            required=False,
                            default=self.config.default_server_port,
                            help='The port to bind to')
        parser.set_defaults(cmd=self.start)

    def start(self, args: argparse.Namespace) -> int:
        self._runtime.late_init(server=True)
        app = fastapi.FastAPI(title='Kaso Mashin API',
                              summary='APIs for the Kaso Mashin controllers',
                              description='Provides APIs for the Kaso Mashin controllers',
                              version=__version__)
        app.include_router(ConfigAPI(self._runtime).router, prefix='/api/config')
        app.include_router(TaskAPI(self._runtime).router, prefix='/api/tasks')
        app.include_router(IdentityAPI(self._runtime).router, prefix='/api/identities')
        app.include_router(NetworkAPI(self._runtime).router, prefix='/api/networks')
        app.include_router(ImageAPI(self._runtime).router, prefix='/api/images')
        app.include_router(InstanceAPI(self._runtime).router, prefix='/api/instances')

        @app.exception_handler(KasoMashinException)
        async def kaso_mashin_exception_handler(request: fastapi.Request, exc: KasoMashinException):
            return fastapi.responses.JSONResponse(
                status_code=exc.status,
                content={'status': exc.status, 'message': exc.msg})

        uvicorn.run(app, host=args.host, port=args.port)
        return 0
