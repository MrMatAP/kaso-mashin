import pytest
import logging
import pathlib
import tempfile
import collections
import shutil
import fastapi
import fastapi.testclient
import sqlalchemy
import sqlalchemy.orm

from kaso_mashin.common.config import Config
from kaso_mashin.server.run import create_server
from kaso_mashin.server.db import DB
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common.model import (
    IdentityKind, IdentityModel)

from kaso_mashin.common.ddd import Base as DDDBase

KasoTestContext = collections.namedtuple('KasoTestContext', 'runtime client')
KasoIdentity = collections.namedtuple('KasoIdentity',
                                      'name kind gecos homedir shell pubkey passwd')

seed = {
    'identities': [
        KasoIdentity(name='Test 1',
                     kind=IdentityKind.PUBKEY,
                     gecos='Test Identity 1',
                     homedir='/home/test1',
                     shell='/bin/bash',
                     pubkey='ssh-rsa test1-pubkey',
                     passwd=None),
        KasoIdentity(name='Test 2',
                     kind=IdentityKind.PUBKEY,
                     gecos=None,
                     homedir=None,
                     shell=None,
                     pubkey='ssh-rsa test2-pubkey',
                     passwd=None),
        KasoIdentity(name='Test 3',
                     kind=IdentityKind.PASSWORD,
                     gecos='Test Identity 3',
                     homedir='/home/test3',
                     shell='/bin/bash',
                     pubkey=None,
                     passwd='foobar')
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
def test_kaso_context_empty() -> KasoTestContext:
    """
    Fixture producing an empty Kaso test context with an api client and direct DB access.
    """
    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix='kaso-test'))
    config_file = temp_dir.joinpath('.kaso')
    with config_file.open('w', encoding='UTF-8') as c:
        c.write(f'path: {temp_dir}')
    config = Config(config_file)
    db = DB(config)
    runtime = Runtime(config=config, db=db)
    server = create_server(runtime)
    logging.getLogger().info(f'Yielding Kaso Mashin context at {temp_dir}')
    yield KasoTestContext(runtime=runtime,
                          client=fastapi.testclient.TestClient(server))
    shutil.rmtree(temp_dir, ignore_errors=True)
    logging.getLogger().info(f'Removed Kaso Mashin context at {temp_dir}')


@pytest.fixture(scope='class')
def test_kaso_context_seeded(test_kaso_context_empty) -> KasoTestContext:
    """
    Fixture producing a fully seeded Kaso test context with an api client and direct DB access
    """
    for kind, entries in seed.items():
        for model in entries:
            test_kaso_context_empty.runtime.db.session.add(IdentityModel(name=model.name,
                                                                         kind=model.kind,
                                                                         gecos=model.gecos,
                                                                         homedir=model.homedir,
                                                                         shell=model.shell,
                                                                         pubkey=model.pubkey,
                                                                         passwd=model.passwd))
    test_kaso_context_empty.runtime.db.session.commit()
    logging.getLogger().info(f'Yielding seeded Kaso Mashin context')
    yield test_kaso_context_empty


@pytest.fixture(scope='module')
def ddd_session() -> sqlalchemy.orm.Session:
    db = pathlib.Path(__file__).parent.joinpath('build/ddd.sqlite')
    db.parent.mkdir(parents=True, exist_ok=True)
    engine = sqlalchemy.create_engine('sqlite:///{}'.format(db), echo=False)
    DDDBase.metadata.create_all(engine)
    session = sqlalchemy.orm.Session(engine)
    yield session
    session.close()
