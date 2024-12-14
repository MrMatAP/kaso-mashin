import ipaddress
import pathlib
import shutil
import subprocess

import pytest
import pytest_asyncio

import pytest_httpserver

import kaso_mashin
import kaso_mashin.base
import kaso_mashin.domain
import kaso_mashin.services
from kaso_mashin.services.db_service import DB


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

@pytest_asyncio.fixture(scope='session')
async def config_service(home: pathlib.Path):
    config_file = home.joinpath('kaso-test.config')
    try:
        config_file.write_text(f'''
        path: {home}
        images_path: {home.joinpath('images')}
        instances_path: {home.joinpath('instances')}
        bootstrap_path: {home.joinpath('bootstrap')}
        ''')
        yield kaso_mashin.services.ConfigService(config_file)
    finally:
        config_file.unlink(missing_ok=True)

@pytest_asyncio.fixture(scope="session")
def db_service(config_service) -> pathlib.Path:
    yield DB(config_service)

@pytest_asyncio.fixture(scope="session")
async def task_service(home) -> kaso_mashin.services.TaskService:
    yield kaso_mashin.services.TaskService()

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
async def identity_repository(db_service, config_service, task_service) -> kaso_mashin.domain.IdentityRepository:
    repo = kaso_mashin.domain.IdentityRepository(db_service, config_service, task_service)
    await repo.initialise()
    yield repo
    await repo.shutdown()

@pytest_asyncio.fixture(scope='function')
async def image_repository(db_service, config_service, task_service) -> kaso_mashin.domain.ImageRepository:
    repo = kaso_mashin.domain.ImageRepository(db_service, config_service, task_service)
    await repo.initialise()
    yield repo
    await repo.shutdown()

@pytest_asyncio.fixture(scope='function')
async def disk_repository(db_service, config_service, task_service) -> kaso_mashin.domain.DiskRepository:
    repo = kaso_mashin.domain.DiskRepository(db_service, config_service, task_service)
    await repo.initialise()
    yield repo
    await repo.shutdown()

@pytest_asyncio.fixture(scope='function')
async def network_repository(db_service, config_service, task_service) -> kaso_mashin.domain.NetworkRepository:
    repo = kaso_mashin.domain.NetworkRepository(db_service, config_service, task_service)
    await repo.initialise()
    yield repo
    await repo.shutdown()

@pytest_asyncio.fixture(scope='function')
async def bootstrap_repository(db_service, config_service, task_service) -> kaso_mashin.domain.BootstrapRepository:
    repo = kaso_mashin.domain.BootstrapRepository(db_service, config_service, task_service)
    await repo.initialise()
    yield repo
    await repo.shutdown()

@pytest_asyncio.fixture(scope='function')
async def identity_seed(identity_repository: kaso_mashin.domain.IdentityRepository) -> kaso_mashin.domain.Identity:
    identity = kaso_mashin.domain.Identity(name='Seed Identity',
                                           kind=kaso_mashin.domain.IdentityKind.PUBKEY)
    identity.gecos = 'Seed Identity'
    await identity.save()
    yield identity
    try:
        await identity_repository.remove(identity)
    except kaso_mashin.base.EntityNotFoundException:
        pass    # We ignore identities that have already been removed

@pytest_asyncio.fixture(scope='function')
async def image_seed(home: pathlib.Path,
                     image_mock_server: pytest_httpserver.HTTPServer,
                     image_repository: kaso_mashin.domain.ImageRepository) -> kaso_mashin.domain.Image:
    image_path = home.joinpath('images').joinpath('seed.qcow2')
    img = kaso_mashin.domain.Image(name='Seed Image',
                url=image_mock_server.url_for('/image.img'))
    await img.save()
    yield img
    try:
        await image_repository.remove(img)
        image_path.unlink(missing_ok=True)
    except kaso_mashin.base.EntityNotFoundException:
        pass    # We ignore images that have already been removed

@pytest_asyncio.fixture(scope='function')
async def disk_seed(home: pathlib.Path,
                    disk_repository: kaso_mashin.domain.DiskRepository) -> kaso_mashin.domain.Disk:
    disk_path = home.joinpath('disks').joinpath('seed.qcow2')
    disk = kaso_mashin.domain.Disk(name='Seed Disk',
                path=disk_path,
                size=kaso_mashin.base.BinarySizedValue(1, kaso_mashin.base.BinaryScale.M))
    await disk.save()
    yield disk
    try:
        await disk_repository.remove(disk)
        disk_path.unlink(missing_ok=True)
    except kaso_mashin.base.EntityNotFoundException:
        pass    # We ignore disks that have already been removed

@pytest_asyncio.fixture(scope='function')
async def network_seed(network_repository: kaso_mashin.domain.NetworkRepository) -> kaso_mashin.domain.Network:
    net = kaso_mashin.domain.Network(name='Seed Network',
                  kind=kaso_mashin.domain.NetworkKind.VMNET_BRIDGED,
                  cidr=ipaddress.IPv4Network('172.16.0.0/24'),
                  gateway=ipaddress.IPv4Address('172.16.0.1'))
    await net.save()
    yield net
    try:
        await network_repository.remove(net)
    except kaso_mashin.base.EntityNotFoundException:
        pass    # We ignore networks that have already been removed

@pytest_asyncio.fixture(scope='function')
async def bootstrap_seed(bootstrap_repository: kaso_mashin.domain.BootstrapRepository) -> kaso_mashin.domain.Bootstrap:
    bootstrap = kaso_mashin.domain.Bootstrap(name='Test',
                          kind=kaso_mashin.domain.BootstrapKind.IGNITION,
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
    except kaso_mashin.base.EntityNotFoundException:
        pass    # We ignore bootstraps that have already been removed
