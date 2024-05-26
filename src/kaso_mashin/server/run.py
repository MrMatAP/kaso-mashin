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

from kaso_mashin import (
    __version__,
    console,
    default_config_file,
    KasoMashinException,
    __log_config__,
)
from kaso_mashin.common.config import Config
from kaso_mashin.common.base_types import ExceptionSchema, CLIArgumentsHolder
from kaso_mashin.common import EntityNotFoundException, EntityInvariantException
from kaso_mashin.server.db import DB
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.server.apis import (
    ConfigAPI,
    TaskAPI,
    ImageAPI,
    DiskAPI,
    NetworkAPI,
    InstanceAPI,
    BootstrapAPI,
    IdentityAPI,
)


def create_server(runtime: Runtime) -> fastapi.applications.FastAPI:
    app = fastapi.FastAPI(
        title="Kaso Mashin API",
        summary="APIs for the Kaso Mashin controllers",
        description="Provides APIs for the Kaso Mashin controllers",
        version=__version__,
        lifespan=runtime.lifespan,
    )

    app.include_router(ConfigAPI(runtime).router, prefix="/api/config")
    app.include_router(TaskAPI(runtime).router, prefix="/api/tasks")
    app.include_router(IdentityAPI(runtime).router, prefix="/api/identities")
    app.include_router(NetworkAPI(runtime).router, prefix="/api/networks")
    app.include_router(ImageAPI(runtime).router, prefix="/api/images")
    app.include_router(DiskAPI(runtime).router, prefix="/api/disks")
    app.include_router(InstanceAPI(runtime).router, prefix="/api/instances")
    app.include_router(BootstrapAPI(runtime).router, prefix="/api/bootstraps")

    app.mount(
        path="/",
        app=fastapi.staticfiles.StaticFiles(
            directory=pathlib.Path(os.path.dirname(__file__), "static")
        ),
        name="static",
    )

    @app.middleware("common-headers")
    async def common_headers(request: fastapi.Request, call_next):
        response: fastapi.Response = await call_next(request)
        response.headers["X-Version"] = __version__
        return response

    @app.exception_handler(KasoMashinException)
    async def kaso_mashin_exception_handler(
        request: fastapi.Request, exc: KasoMashinException
    ):
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
            content=ExceptionSchema(status=exc.status, msg=f"{exc.msg}").model_dump(),
        )

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
            content=ExceptionSchema(status=exc.status, msg=f"{exc.msg}").model_dump(),
        )

    @app.exception_handler(sqlalchemy.exc.SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: fastapi.Request, exc: sqlalchemy.exc.SQLAlchemyError
    ):
        del request  # pylint: disable=unused-argument
        logging.getLogger("kaso_mashin.server").error(
            "(500) Database exception %s", str(exc)
        )
        return fastapi.responses.JSONResponse(
            status_code=500,
            content=ExceptionSchema(
                status=500, msg=f"Database exception {exc}"
            ).model_dump(),
        )

    return app


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the server

    Returns:
        An exit code. 0 when successful, non-zero otherwise
    """
    logger = logging.getLogger("kaso_mashin.server")
    config = Config()
    db = DB(config)
    runtime = Runtime(config=config, db=db)

    parsed_args = CLIArgumentsHolder(config=config)
    parser = argparse.ArgumentParser(
        add_help=True, description=f"kaso-server - {__version__}"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", dest="debug", help="Debug"
    )
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
    config.load(parsed_args.config)
    config.cli_override(parsed_args)
    try:
        app = create_server(runtime)
        uvicorn.run(
            app,
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
