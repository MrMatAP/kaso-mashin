import ipaddress
import pathlib
import shutil
import subprocess

import pytest
import pytest_asyncio

import pytest_httpserver
import sqlalchemy.ext.asyncio

from kaso_mashin.common import (
    EntityNotFoundException,
    BinarySizedValue, BinaryScale,
    TaskService, ConfigService,
    Model,
    Identity, IdentityRepository, IdentityKind,
    Image, ImageRepository,
    Disk, DiskRepository,
    Network, NetworkRepository, NetworkKind,
    Bootstrap, BootstrapRepository, BootstrapKind
)

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
async def identity_repository(async_session_maker, config_service, task_service) -> IdentityRepository:
    return IdentityRepository(async_session_maker, config_service, task_service)

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
async def identity_seed(identity_repository: IdentityRepository) -> Identity:
    identity = Identity(name='Seed Identity', kind=IdentityKind.PUBKEY)
    identity.gecos = 'Seed Identity'
    await identity.save()
    yield identity
    try:
        await identity_repository.remove(identity)
    except EntityNotFoundException:
        pass    # We ignore identities that have already been removed

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

@pytest_asyncio.fixture(scope='function')
async def bootstrap_seed(bootstrap_repository: BootstrapRepository) -> Bootstrap:
    bootstrap = Bootstrap(name='Test',
                          kind=BootstrapKind.IGNITION,
                          content='''
                          version: 1.0.0
                          variant: flatcar
                          files:
                          - path: /etc/hostname
                            mode: 0644
                            overwrite: true
                            contents:
                              inline: |
                                {{ name }}
                          ''')
    await bootstrap.save()
    yield bootstrap
    try:
        await bootstrap_repository.remove(bootstrap)
    except EntityNotFoundException:
        pass    # We ignore bootstraps that have already been removed
