import sys
import os
import typing
import logging
import pathlib
import argparse

import fastapi
import fastapi.staticfiles
import uvicorn
import sqlalchemy.exc

from kaso_mashin import __version__, console, default_config_file, KasoMashinException
from kaso_mashin.common.config import Config
from kaso_mashin.common.model import ExceptionSchema
from kaso_mashin.server.db import DB
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.server.apis import ConfigAPI, TaskAPI, ImageAPI, IdentityAPI, NetworkAPI, InstanceAPI


def create_server(runtime: Runtime) -> fastapi.applications.FastAPI:
    app = fastapi.FastAPI(title='Kaso Mashin API',
                          summary='APIs for the Kaso Mashin controllers',
                          description='Provides APIs for the Kaso Mashin controllers',
                          version=__version__)

    app.include_router(ConfigAPI(runtime).router, prefix='/api/config')
    app.include_router(TaskAPI(runtime).router, prefix='/api/tasks')
    app.include_router(IdentityAPI(runtime).router, prefix='/api/identities')
    app.include_router(NetworkAPI(runtime).router, prefix='/api/networks')
    app.include_router(ImageAPI(runtime).router, prefix='/api/images')
    app.include_router(InstanceAPI(runtime).router, prefix='/api/instances')
    app.mount(path='/',
              app=fastapi.staticfiles.StaticFiles(directory=pathlib.Path(os.path.dirname(__file__), 'static')),
              name='static')

    @app.middleware('common-headers')
    async def common_headers(request: fastapi.Request, call_next):
        response: fastapi.Response = await call_next(request)
        response.headers['X-Version'] = __version__
        return response

    @app.exception_handler(KasoMashinException)
    async def kaso_mashin_exception_handler(request: fastapi.Request, exc: KasoMashinException):
        del request  # pylint: disable=unused-argument
        logging.getLogger('kaso_mashin.server').error('(%s) %s', exc.status, exc.msg)
        return fastapi.responses.JSONResponse(status_code=exc.status,
                                              content=ExceptionSchema(status=exc.status, msg=exc.msg)
                                              .model_dump())

    @app.exception_handler(sqlalchemy.exc.SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: fastapi.Request, exc: sqlalchemy.exc.SQLAlchemyError):
        del request  # pylint: disable=unused-argument
        logging.getLogger('kaso_mashin.server').error('(500) Database exception %s', str(exc))
        return fastapi.responses.JSONResponse(status_code=500,
                                              content=ExceptionSchema(status=500, msg=f'Database exception {exc}')
                                              .model_dump())

    return app


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the server

    Returns:
        An exit code. 0 when successful, non-zero otherwise
    """
    logger = logging.getLogger('kaso_mashin.server')
    config = Config()
    db = DB(config)
    runtime = Runtime(config=config, db=db)

    parser = argparse.ArgumentParser(add_help=True, description=f'kaso-server - {__version__}')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug')
    parser.add_argument('-c', '--config',
                        dest='config',
                        type=pathlib.Path,
                        required=False,
                        default=default_config_file,
                        help=f'Path to the configuration file. Defaults to {default_config_file}')
    parser.add_argument('--host',
                        dest='default_server_host',
                        type=str,
                        required=False,
                        default=config.default_server_host,
                        help='The host to bind to')
    parser.add_argument('--port',
                        dest='default_server_port',
                        type=int,
                        required=False,
                        default=config.default_server_port,
                        help='The port to bind to')

    args = parser.parse_args(args if args is not None else sys.argv[1:])
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    config.load(args.config)
    config.cli_override(args)
    # TODO: We should move this into config
    runtime.late_init(server=True)
    try:
        logger.info('Effective user %s', runtime.effective_user)
        logger.info('Owning user %s', runtime.owning_user)
        app = create_server(runtime)
        uvicorn.run(app, host=config.default_server_host, port=config.default_server_port)
        return 0
    except Exception:  # pylint: disable=broad-except
        console.print_exception()
    return 1


if __name__ == '__main__':
    sys.exit(main())
