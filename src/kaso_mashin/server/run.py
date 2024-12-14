import sys
import typing
import logging
import pathlib
import argparse
import contextlib
import shutil

import fastapi
import fastapi.staticfiles
# TODO: Temporarily until we figure out the VNC proxy issues
import fastapi.middleware.cors
import uvicorn
import sqlalchemy.ext.asyncio
import sqlalchemy.exc
import asyncio

from starlette.middleware.cors import CORSMiddleware

from kaso_mashin import __version__, console, __log_config__
from kaso_mashin.base import (
    ExceptionSchema,
    KasoMashinException,
    EntityNotFoundException,
    EntityInvariantException)
import kaso_mashin.domain
import kaso_mashin.services
from kaso_mashin.services.db_service import DB
from kaso_mashin.server.apis import (
    identity_router,
    image_router,
    disk_router,
    bootstrap_router,
)
logger = logging.getLogger("kaso_mashin.server")


class KasoServer:

    def __init__(self, config: kaso_mashin.services.ConfigService):
        self._config = config
        self._db = DB(config)
        self._task_service = kaso_mashin.services.TaskService()

    def start(self):
        app = fastapi.FastAPI(
            title="Kaso Mashin API",
            summary="APIs for the Kaso Mashin controllers",
            description="Provides APIs for the Kaso Mashin controllers",
            version=__version__,
            lifespan=self._lifespan,
        )
        # TODO: Temporarily until we figure out the VNC issues
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"])

        # app.include_router(TaskAPI(runtime).router, prefix="/api/tasks")
        # app.include_router(NetworkAPI(runtime).router, prefix="/api/networks")
        # app.include_router(ImageAPI(runtime).router, prefix="/api/images")
        # app.include_router(InstanceAPI(runtime).router, prefix="/api/instances")
        app.include_router(identity_router, prefix='/api/identities')
        app.include_router(image_router, prefix='/api/images')
        app.include_router(disk_router, prefix='/api/disks')
        app.include_router(bootstrap_router, prefix='/api/bootstraps')

        @app.websocket('/api/console/{uid}')
        async def vconsole(uid: str, websocket: fastapi.WebSocket) -> None:
            unix_writer = None
            try:
                await websocket.accept()
                logger.info('Accepted websocket connection')

                logger.info("Opening VNC socket")
                unix_reader, unix_writer = await asyncio.open_unix_connection(
                    path='/Users/imfeldma/var/kaso/instances/vnctest/vconsole.sock')
                logger.info('VNC Proxy starting to serve')
                while True:
                    data_out = await unix_reader.read(n=4096)
                    logger.info(f'VNC Proxy relaying {len(data_out)} output bytes')
                    await websocket.send_bytes(data_out)
                    data_in = await websocket.receive_bytes()
                    logger.info(f"VNC Proxy relaying {len(data_in)} input bytes")
                    unix_writer.write(data_in)
                    await unix_writer.drain()

            except fastapi.WebSocketDisconnect:
                logger.info('WebSocket disconnected')
            except fastapi.WebSocketException as e:
                logger.info('WebSocket exception: ' + str(e))
            except Exception as e:
                logging.getLogger("kaso_mashin.server").error('Failed to open socket: ' + str(e))
            finally:
                if unix_writer is not None:
                    unix_writer.close()
                    await unix_writer.wait_closed()
                    logger.info('UNIX socket closed')

        @app.middleware("common-headers")
        async def common_headers(request: fastapi.Request, call_next):
            response: fastapi.Response = await call_next(request)
            response.headers["X-Version"] = __version__
            return response

        @app.exception_handler(KasoMashinException)
        async def kaso_mashin_exception_handler(request: fastapi.Request, exc: KasoMashinException):
            del request
            logging.getLogger("kaso_mashin.server").error(
                "(%s) %s", exc.status, f"{exc.__class__.__name__}: {exc.msg}"
            )
            return fastapi.responses.JSONResponse(
                status_code=exc.status,
                content=ExceptionSchema(status=exc.status, msg=f"{exc.msg}").model_dump(),
            )

        @app.exception_handler(EntityNotFoundException)
        async def entity_not_found_exception_handler(
                request: fastapi.Request, exc: EntityNotFoundException
        ):
            del request
            logging.getLogger("kaso_mashin.server").error(
                "(%s) %s", exc.status, f"{exc.__class__.__name__}: {exc.msg}"
            )
            return fastapi.responses.JSONResponse(
                status_code=exc.status,
                content=ExceptionSchema.model_validate(exc))

        @app.exception_handler(EntityInvariantException)
        async def entity_invariant_exception_handler(
                request: fastapi.Request, exc: EntityInvariantException
        ):
            del request
            logging.getLogger("kaso_mashin.server").error(
                "(%s) %s", exc.status, f"{exc.__class__.__name__}: {exc.msg}"
            )
            return fastapi.responses.JSONResponse(
                status_code=exc.status,
                content=ExceptionSchema.model_validate(exc))

        @app.exception_handler(sqlalchemy.exc.SQLAlchemyError)
        async def sqlalchemy_exception_handler(
                request: fastapi.Request, exc: sqlalchemy.exc.SQLAlchemyError
        ):
            del request  # pylint: disable=unused-argument
            logging.getLogger("kaso_mashin.server").error("(500) Database exception %s", str(exc))
            return fastapi.responses.JSONResponse(
                status_code=500,
                content=ExceptionSchema.model_validate(exc))

        # TODO: Re-enable this once websocket/static file stuff is solved
        # app.mount(
        #     path="/",
        #     app=fastapi.staticfiles.StaticFiles(
        #         directory=pathlib.Path(os.path.dirname(__file__), "static")
        #     ),
        #     name="static",
        # )

        return app

    @contextlib.asynccontextmanager
    async def _lifespan(self, app: fastapi.FastAPI):
        del app
        for path in (self._config.path,
                     self._config.images_path,
                     self._config.instances_path,
                     self._config.bootstrap_path):
            path.mkdir(parents=True, exist_ok=True)
            shutil.chown(path=path, user=self._config.owning_user)
        repositories = {kaso_mashin.domain.ImageRepository: None,
                        kaso_mashin.domain.DiskRepository: None,
                        kaso_mashin.domain.IdentityRepository: None,
                        kaso_mashin.domain.InstanceRepository: None,
                        kaso_mashin.domain.NetworkRepository: None,
                        kaso_mashin.domain.BootstrapRepository: None}
        for clazz in repositories.keys():
            repositories[clazz] = clazz(db_service=self._db,
                                        config_service=self._config,
                                        task_service=self._task_service)
            await repositories[clazz].initialise()
        yield
        for instance in repositories.values():
            await instance.shutdown()


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the server

    Returns:
        An exit code. 0 when successful, non-zero otherwise
    """
    config = kaso_mashin.services.ConfigService()

    parsed_args = kaso_mashin.services.CLIArgumentsHolder(config=config)
    parser = argparse.ArgumentParser(add_help=True, description=f"kaso-server - {__version__}")
    parser.add_argument("-d", "--debug", action="store_true", dest="debug", help="Debug")
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        type=pathlib.Path,
        required=False,
        default=parsed_args.config,
        help=f"Path to the configuration file. Defaults to {parsed_args.config}",
    )
    parser.add_argument(
        "--host",
        dest="default_server_host",
        type=str,
        required=False,
        default=parsed_args.host,
        help="The host to bind to",
    )
    parser.add_argument(
        "--port",
        dest="default_server_port",
        type=int,
        required=False,
        default=parsed_args.port,
        help="The port to bind to",
    )

    parser.parse_args(args if args is not None else sys.argv[1:], namespace=parsed_args)
    logger.setLevel(logging.DEBUG if parsed_args.debug else logging.INFO)
    logger.debug('Logging at DEBUG level')
    config.load(parsed_args.config)
    config.cli_override(parsed_args)
    try:
        server = KasoServer(config)
        uvicorn.run(
            server.start(),
            host=config.default_server_host,
            port=config.default_server_port,
            log_config=__log_config__,
        )
        return 0
    except KeyboardInterrupt:
        console.print("Shutting down...")
    except Exception:  # pylint: disable=broad-except
        console.print_exception()
    return 1


if __name__ == "__main__":
    sys.exit(main())
