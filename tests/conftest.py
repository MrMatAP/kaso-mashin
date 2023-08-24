import pytest
import shutil
import fastapi
import fastapi.testclient

from kaso_mashin import __version__, KasoMashinException
from kaso_mashin.common.config import Config
from kaso_mashin.server.db import DB
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import (
    IdentityKind, IdentityModel)
from kaso_mashin.server.apis import (
    ConfigAPI, TaskAPI, IdentityAPI, NetworkAPI, ImageAPI, InstanceAPI
)

seed = {
    'identities': [
        IdentityModel(name='Test 1', kind=IdentityKind.PUBKEY,
                      gecos='Test Identity 1', homedir='/home/test1', shell='/bin/bash', pubkey='ssh-rsa test1-pubkey'),
        IdentityModel(name='Test 2', kind=IdentityKind.PUBKEY,
                      pubkey='ssh-rsa test2-pubkey'),
        IdentityModel(name='Test 3', kind=IdentityKind.PASSWORD,
                      gecos='Test Identity 3', homedir='/home/test3', shell='/bin/bash', passwd='foobar')
    ],
    # 'networks': [
    #     NetworkModel(name='test-network-0',
    #                  kind=NetworkKind.VMNET_HOST,
    #                  host_ip4='172.16.100.10',
    #                  nm4='255.255.255.0',
    #                  gw4='172.16.100.1',
    #                  ns4='172.16.100.1',
    #                  host_phone_home_port=10200),
    #     NetworkModel(name='test-network-1',
    #                  kind=NetworkKind.VMNET_SHARED,
    #                  host_ip4='172.16.101.10',
    #                  nm4='255.255.255.0',
    #                  gw4='172.16.101.1',
    #                  ns4='8.8.8.8',
    #                  host_phone_home_port=8000)
    # ],
    # 'images': [
    #     ImageModel(name='ubuntu-jammy', path='/no/where/jammy.qcow2'),
    #     ImageModel(name='freebsd14', path='/no/where/freebsd14.qcow2',
    #                min_cpu=2, min_ram=2048, min_space='10G'),
    #     ImageModel(name='ubuntu-kinetic', path='/no/where/kinetic.qcow2',
    #                min_cpu=2, min_ram=4096, min_space='2G')
    # ]
}


@pytest.fixture(scope='class')
def class_temp_dir(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp('pytest')
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope='class')
def test_config(class_temp_dir):
    config_file = class_temp_dir.joinpath('.kaso')
    with config_file.open('w', encoding='UTF-8') as c:
        c.write(f'path: {class_temp_dir}')
    return Config(config_file=config_file)


@pytest.fixture(scope='class')
def test_db(test_config):
    return DB(config=test_config)


@pytest.fixture(scope='class')
def test_runtime(test_config, test_db):
    return Runtime(config=test_config, db=test_db)


def test_api_server(test_runtime):
    app = fastapi.FastAPI(title='Kaso Mashin API',
                          summary='APIs for the Kaso Mashin controllers',
                          description='Provides APIs for the Kaso Mashin controllers',
                          version=__version__)
    app.include_router(ConfigAPI(test_runtime).router, prefix='/api/config')
    app.include_router(TaskAPI(test_runtime).router, prefix='/api/tasks')
    app.include_router(IdentityAPI(test_runtime).router, prefix='/api/identities')
    app.include_router(NetworkAPI(test_runtime).router, prefix='/api/networks')
    app.include_router(ImageAPI(test_runtime).router, prefix='/api/images')
    app.include_router(InstanceAPI(test_runtime).router, prefix='/api/instances')

    @app.exception_handler(KasoMashinException)
    async def kaso_mashin_exception_handler(request: fastapi.Request, exc: KasoMashinException):
        return fastapi.responses.JSONResponse(
            status_code=exc.status,
            content={'status': exc.status, 'message': exc.msg})

    return app


@pytest.fixture(scope='class')
def test_api_server_empty(test_runtime):
    app = test_api_server(test_runtime)
    yield app


@pytest.fixture(scope='class')
def test_api_server_seeded(test_runtime):
    app = test_api_server(test_runtime)
    for kind, entries in seed.items():
        for model in entries:
            test_runtime.db.session.add(model)
    test_runtime.db.session.commit()
    yield app


@pytest.fixture(scope='class')
def test_api_client_empty(test_api_server_empty):
    yield fastapi.testclient.TestClient(test_api_server_empty)


@pytest.fixture(scope='class')
def test_api_client_seeded(test_api_server_seeded):
    yield fastapi.testclient.TestClient(test_api_server_seeded)
