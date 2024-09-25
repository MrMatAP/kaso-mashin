import abc
import ipaddress
import typing
import uuid
import collections
import pathlib
import shutil
import logging
import subprocess

import pytest
import pytest_asyncio
import tempfile

import pytest_httpserver
import sqlalchemy.ext.asyncio

import fastapi
import fastapi.testclient

from kaso_mashin.common import (
    EntityNotFoundException,
    UniqueIdentifier, BinarySizedValue, BinaryScale,
    TaskService, ConfigService,
    Image, ImageRepository,
    Disk, DiskRepository, DiskModel, DiskFormat,
    Network, NetworkRepository, NetworkKind, NetworkModel,
    Bootstrap, BootstrapRepository,
    IdentityModel, IdentityKind
)

from kaso_mashin.server.run import create_server
from kaso_mashin.server.db import DB
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common import (
    Model, T_Model,
    T_Entity,
    T_EntityListSchema,
    T_EntityGetSchema
)

KasoTestContext = collections.namedtuple("KasoTestContext", "config db runtime server client")


class BaseTest(typing.Generic[T_Model, T_Entity, T_EntityGetSchema], abc.ABC):

    @staticmethod
    def find_match_in_seeds(
        uid: UniqueIdentifier, seeds: typing.List[T_Model]
    ) -> T_Model:
        matches = list(filter(lambda s: s.uid == str(uid), seeds))
        assert len(matches) == 1
        return matches[0]

    @abc.abstractmethod
    def assert_get_by_model(self, obj: T_EntityGetSchema | T_Entity, model: T_Model):
        pass

    @abc.abstractmethod
    def assert_list_by_model(self, obj: T_EntityListSchema | T_Entity, model: T_Model):
        pass


seed = {
    "identities": [
        IdentityModel(
            uid=str(uuid.uuid4()),
            name="Test Identity 1",
            kind=IdentityKind.PUBKEY,
            gecos="Test Identity 1",
            homedir="/home/test1",
            shell="/bin/bash",
            credential="ssh-rsa test1-pubkey",
        ),
        IdentityModel(
            uid=str(uuid.uuid4()),
            name="Test Identity 2",
            kind=IdentityKind.PUBKEY,
            gecos="Test Identity 2",
            homedir="/home/test2",
            shell="/bin/bash",
            credential="ssh-rsa test2-pubkey",
        ),
        IdentityModel(
            uid=str(uuid.uuid4()),
            name="Test Identity 3",
            kind=IdentityKind.PASSWORD,
            gecos="Test Identity 3",
            homedir="/home/test3",
            shell="/bin/bash",
            credential="foobar",
        ),
    ],
    "networks": [
        NetworkModel(
            uid=str(uuid.uuid4()),
            name="Test Network 1",
            kind=NetworkKind.VMNET_SHARED,
            cidr="10.0.0.0/24",
            gateway="10.0.0.1",
            dhcp_start="10.0.0.2",
            dhcp_end="10.0.0.254",
        ),
        NetworkModel(
            uid=str(uuid.uuid4()),
            name="Test Network 2",
            kind=NetworkKind.VMNET_HOST,
            cidr="10.0.1.0/24",
            gateway="10.0.1.1",
            dhcp_start="10.0.1.2",
            dhcp_end="10.0.1.254",
        ),
        NetworkModel(
            uid=str(uuid.uuid4()),
            name="Test Network 3",
            kind=NetworkKind.VMNET_BRIDGED,
            cidr="10.0.2.0/24",
            gateway="10.0.2.1",
            dhcp_start="10.0.2.2",
            dhcp_end="10.0.2.254",
        ),
    ],
    "disks": [
        DiskModel(
            uid=str(uuid.uuid4()),
            name="Test Disk 1",
            path="/no/where",
            size=1,
            size_scale=BinaryScale.M,
            disk_format=DiskFormat.Raw,
        )
    ],
}


@pytest.mark.asyncio
@pytest_asyncio.fixture(scope="session")
async def test_context_empty() -> KasoTestContext:
    """
    Fixture producing an empty Kaso test context
    """
    temp_dir = pathlib.Path(
        tempfile.mkdtemp(
            prefix="kaso-test",
            dir=pathlib.Path(__file__).parent.parent.joinpath("build"),
        )
    )
    config_file = temp_dir.joinpath(".kaso")
    with config_file.open("w", encoding="UTF-8") as c:
        c.write(f"path: {temp_dir}")
    config = ConfigService(config_file)
    db = DB(config)
    runtime = Runtime(config=config, db=db)
    server = create_server(runtime)
    async with runtime.lifespan(app=server):
        logging.getLogger().info(f"Yielding empty Kaso Mashin context at {temp_dir}")
        yield KasoTestContext(
            config=config,
            db=db,
            runtime=runtime,
            server=server,
            client=fastapi.testclient.TestClient(server),
        )
    shutil.rmtree(temp_dir, ignore_errors=True)
    logging.getLogger().info(f"Removed empty Kaso Mashin context at {temp_dir}")


@pytest.mark.asyncio
@pytest_asyncio.fixture(scope="session")
async def test_context_seeded() -> KasoTestContext:
    """
    Fixture producing a fully seeded Kaso test context
    """
    temp_dir = pathlib.Path(
        tempfile.mkdtemp(
            prefix="kaso-test",
            dir=pathlib.Path(__file__).parent.parent.joinpath("build"),
        )
    )
    config_file = temp_dir.joinpath(".kaso")
    with config_file.open("w", encoding="UTF-8") as c:
        c.write(f"path: {temp_dir}")
    config = ConfigService(config_file)
    db = DB(config)
    runtime = Runtime(config=config, db=db)
    server = create_server(runtime)
    session_maker = await db.async_sessionmaker
    async with session_maker() as session:
        for kind, entries in seed.items():
            for model in entries:
                session.add(model)
        await session.commit()
    async with runtime.lifespan(app=server):
        logging.getLogger().info(f"Yielding seeded Kaso Mashin context at {temp_dir}")
        yield KasoTestContext(
            config=config,
            db=db,
            runtime=runtime,
            server=server,
            client=fastapi.testclient.TestClient(server),
        )
    shutil.rmtree(temp_dir, ignore_errors=True)
    logging.getLogger().info(f"Removed seeded Kaso Mashin context at {temp_dir}")

#
# New fixtures start here

def qemu_img_available() -> bool:
    return pathlib.Path('/opt/homebrew/bin/qemu-img').exists()

@pytest.fixture(scope='session')
def qemu_img_executable() -> pathlib.Path:
    return pathlib.Path('/opt/homebrew/bin/qemu-img')

@pytest.fixture(scope='session')
def home() -> pathlib.Path:
    h = pathlib.Path(__file__).parent.parent.joinpath('build/kaso-test')
    h.mkdir(parents=True, exist_ok=True)
    h.joinpath('images').mkdir(exist_ok=True)
    h.joinpath('mock').mkdir(exist_ok=True)
    yield h
    shutil.rmtree(h, ignore_errors=True)

@pytest.fixture(scope="session")
def db(home) -> pathlib.Path:
    f = home.joinpath('kaso-test.sqlite')
    f.parent.mkdir(parents=True, exist_ok=True)
    yield f
    f.unlink(missing_ok=True)

@pytest_asyncio.fixture(scope="session")
def task_service(home) -> TaskService:
    yield TaskService()

@pytest_asyncio.fixture(scope='function')
async def async_session_maker(db) -> sqlalchemy.ext.asyncio.async_sessionmaker[
    sqlalchemy.ext.asyncio.AsyncSession]:
    engine = sqlalchemy.ext.asyncio.create_async_engine(f'sqlite+aiosqlite:///{db}',
                                                        echo=False)
    asm = sqlalchemy.ext.asyncio.async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    yield asm
    await engine.dispose()

@pytest_asyncio.fixture(scope='function')
async def image_mock_server(home: pathlib.Path,
                            qemu_img_executable: pathlib.Path,
                            httpserver: pytest_httpserver.HTTPServer):
    mock_image = home.joinpath('mock').joinpath('image.img')
    subprocess.run([qemu_img_executable, 'create', '-q', '-f', 'qcow2', mock_image, '1M'])
    with open(mock_image, 'rb') as img:
        img_data = img.read()
    httpserver.expect_request('/image.img').respond_with_data(
        img_data,
        content_type='application/octet-stream')
    yield httpserver
    mock_image.unlink(missing_ok=True)

@pytest_asyncio.fixture(scope='function')
async def config_service(home: pathlib.Path):
    config_file = home.joinpath('kaso-test.config')
    try:
        config_file.write_text(f'''
        path: {home}
        images_path: {home.joinpath('images')}
        instances_path: {home.joinpath('instances')}
        bootstrap_path: {home.joinpath('bootstrap')}
        ''')
        yield ConfigService(config_file)
    finally:
        config_file.unlink(missing_ok=True)

@pytest_asyncio.fixture(scope='function')
async def task_service():
    yield TaskService()

@pytest_asyncio.fixture(scope='function')
async def image_repository(async_session_maker, config_service, task_service) -> ImageRepository:
    return ImageRepository(async_session_maker, config_service, task_service)

@pytest_asyncio.fixture(scope='function')
async def disk_repository(async_session_maker, config_service, task_service) -> DiskRepository:
    return DiskRepository(async_session_maker, config_service, task_service)

@pytest_asyncio.fixture(scope='function')
async def network_repository(async_session_maker, config_service, task_service) -> NetworkRepository:
    return NetworkRepository(async_session_maker, config_service, task_service)

@pytest_asyncio.fixture(scope='function')
async def bootstrap_repository(async_session_maker, config_service, task_service) -> BootstrapRepository:
    return BootstrapRepository(async_session_maker, config_service, task_service)

@pytest_asyncio.fixture(scope='function')
async def image_seed(home: pathlib.Path,
                     image_mock_server: pytest_httpserver.HTTPServer,
                     image_repository: ImageRepository) -> Image:
    image_path = home.joinpath('images').joinpath('seed.qcow2')
    img = Image(name='Seed Image',
                url=image_mock_server.url_for('/image.img'),
                path=image_path)
    await img.save()
    yield img
    try:
        await image_repository.remove(img)
        image_path.unlink(missing_ok=True)
    except EntityNotFoundException:
        pass    # We ignore images that have already been removed

@pytest_asyncio.fixture(scope='function')
async def disk_seed(home: pathlib.Path,
                    disk_repository: DiskRepository) -> Disk:
    disk_path = home.joinpath('disks').joinpath('seed.qcow2')
    disk = Disk(name='Seed Disk',
                path=disk_path,
                size=BinarySizedValue(1, BinaryScale.M))
    await disk.save()
    yield disk
    try:
        await disk_repository.remove(disk)
        disk_path.unlink(missing_ok=True)
    except EntityNotFoundException:
        pass    # We ignore disks that have already been removed

@pytest_asyncio.fixture(scope='function')
async def network_seed(network_repository: NetworkRepository) -> Network:
    net = Network(name='Seed Network',
                  kind=NetworkKind.VMNET_BRIDGED,
                  cidr=ipaddress.IPv4Network('172.16.0.0/24'),
                  gateway=ipaddress.IPv4Address('172.16.0.1'))
    await net.save()
    yield net
    try:
        await network_repository.remove(net)
    except EntityNotFoundException:
        pass    # We ignore networks that have already been removed
