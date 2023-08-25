import sys
import typing
import logging
import pathlib
import argparse

import fastapi
import uvicorn

from kaso_mashin import __version__, console, default_config_file, KasoMashinException
from kaso_mashin.common.config import Config
from kaso_mashin.server.db import DB
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.server.apis import ConfigAPI, TaskAPI, ImageAPI, IdentityAPI, NetworkAPI, InstanceAPI


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the server

    Returns:
        An exit code. 0 when successful, non-zero otherwise
    """
    logger = logging.getLogger(__name__)
    config = Config(config_file=default_config_file)
    db = DB(config)
    runtime = Runtime(config=config, db=db)

    parser = argparse.ArgumentParser(add_help=True, description=f'kaso-mashin - {__version__}')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug')
    parser.add_argument('-c', '--config',
                        dest='config',
                        type=pathlib.Path,
                        required=False,
                        default=default_config_file,
                        help=f'Path to the configuration file. Defaults to {default_config_file}')
    # TODO: We should keep this in the config file alone
    parser.add_argument('-p', '--path',
                        dest='path',
                        type=pathlib.Path,
                        required=False,
                        default=config.path,
                        help=f'Cloud directory. Defaults to {config.path}')
    parser.add_argument('--host',
                        dest='host',
                        type=str,
                        required=False,
                        default=config.default_server_host,
                        help='The host to bind to')
    parser.add_argument('--port',
                        dest='port',
                        type=int,
                        required=False,
                        default=config.default_server_port,
                        help='The port to bind to')

    args = parser.parse_args(args if args is not None else sys.argv[1:])
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    if args.config:
        config.config_file = args.config
    # TODO: We should not do this here
    if not args.path.exists():
        console.print(f'Creating directory at {args.path}')
        args.path.mkdir(parents=True)
    # TODO: runtime should only ever have to be initialised by the server
    runtime.late_init(server=True)
    try:
        logger.info(f'Effective user {runtime.effective_user}')
        logger.info(f'Owning user {runtime.owning_user}')
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

        @app.exception_handler(KasoMashinException)
        # pylint: disable=unused-argument
        async def kaso_mashin_exception_handler(request: fastapi.Request, exc: KasoMashinException):
            return fastapi.responses.JSONResponse(
                status_code=exc.status,
                content={'status': exc.status, 'message': exc.msg})

        uvicorn.run(app, host=args.host, port=args.port)
        return 0
    except Exception:   # pylint: disable=broad-except
        console.print_exception()
    return 1


if __name__ == '__main__':
    sys.exit(main())