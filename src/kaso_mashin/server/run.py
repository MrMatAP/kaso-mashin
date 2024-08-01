import sys
import os
import typing
import logging
import pathlib
import argparse
import contextlib

import fastapi
import fastapi.staticfiles
import uvicorn
import sqlalchemy.exc
import asyncio
import telnetlib3
from websockets.legacy import async_timeout

from kaso_mashin import (
    __version__,
    console,
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

logger = logging.getLogger("kaso_mashin.server")

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

    @app.websocket_route('/api/console/{uid}')
    async def console(websocket: fastapi.WebSocket) -> None:

        log = logging.getLogger('kaso_mashin.server')
        queue = asyncio.queues.Queue()
        # Inspired by this: https://stackoverflow.com/questions/67947099/send-receive-in-parallel-using-websockets-in-python-fastapi

        async def proxy_input(webs: fastapi.WebSocket, console_writer: asyncio.StreamWriter) -> None:
            async for data in webs.iter_bytes():
                log.info(f'Read {len(data)} bytes of input')
                console_writer.write(data)
                await writer.drain()

        async def proxy_output(webs: fastapi.WebSocket, console_reader: asyncio.StreamReader) -> None:
            data = await console_reader.read()
            await webs.send_bytes(data)

        async def read_from_ws(ws: fastapi.WebSocket) -> None:
            async for data in ws.iter_bytes():
                log.info(f'Read {len(data)} bytes of input')
                queue.put_nowait(data)

        async def get_data_and_send(ws: fastapi.WebSocket) -> None:
            data = await queue.get()
            while True:
                if queue.empty():
                    log.info('Queue is empty')
                else:
                    data = queue.get_nowait()
                    await ws.send_bytes(data)


        try:
            await websocket.accept()
            log.info('Accepted websocket connection')
            reader, writer = await asyncio.open_unix_connection(path='/Users/imfeldma/var/kaso/instances/vnctest/vconsole.sock')
            log.info('Opened AF_UNIX socket')
            log.info('Starting proxying')
            async with asyncio.TaskGroup() as proxyTasks:
                read_from_ws_task = proxyTasks.create_task(read_from_ws(websocket))
                get_data_and_send_task = proxyTasks.create_task(get_data_and_send(websocket))
            log.info('Proxying has finished')
        except fastapi.WebSocketDisconnect:
            log.info('WebSocket disconnected')
        except fastapi.WebSocketException as e:
            log.info('WebSocket exception: ' + str(e))
        except Exception as e:
            logging.getLogger("kaso_mashin.server").error('Failed to open socket: ' + str(e))

        # try:
        #     await websocket.accept()
        #     log.info(f'Console client connected')
        #     server = await asyncio.start_unix_server(proxyhandler,
        #                                              path='/Users/imfeldma/var/kaso/instances/vnctest/vconsole.sock')
        #     log.info('Console server created')
        #     async with server:
        #         log.info('Console server serving forever')
        #         await server.serve_forever()
        #     log.info('Console exiting')
        #

            #
            # An attempt using ProxyHandler
            # class ProxyHandler(asyncio.Protocol):
            #     LOG = logging.getLogger("kaso_mashin.server")
            #
            #     def connection_made(self, transport):
            #         super().connection_made(transport)
            #         self.LOG.info("Connection made")
            #
            #     def data_received(self, data: bytes):
            #         #websocket.send_bytes(data)
            #         self.LOG.info(f'Sent {len(data)} bytes')
            #
            #     def eof_received(self):
            #         #await websocket.close()
            #         self.LOG.info('Closing websocket')
            #

            # (transport, protocol) = await asyncio.get_event_loop().create_unix_connection(ProxyHandler,
            #                                                                               path='/Users/imfeldma/var/kaso/instances/vnctest/vconsole.sock')
            # while True:
            #     data_in = await websocket.receive_bytes()
            #     transport.write(data_in)
            #     await asyncio.sleep(1)

            # with socket.socket(family=socket.AF_UNIX, type=socket.SOCK_STREAM) as console_socket:
            #     console_socket.connect('/Users/imfeldma/var/kaso/instances/vnctest/vconsole.sock')
            #     while True:
            #         data_out = console_socket.recv(4096)
            #         await websocket.send_bytes(data_out)
            #         data_in = await websocket.receive_bytes()
            #         console_socket.send(data_in)

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

    return app


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the server

    Returns:
        An exit code. 0 when successful, non-zero otherwise
    """
    config = Config()
    db = DB(config)
    runtime = Runtime(config=config, db=db)

    parsed_args = CLIArgumentsHolder(config=config)
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
