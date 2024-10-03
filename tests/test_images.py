import pytest

import uuid
import pathlib

import pytest_httpserver

from conftest import qemu_img_available
from kaso_mashin.common import (
    EntityNotFoundException, EntityInvariantException,
    BinarySizedValue, BinaryScale,
    Image, ImageRepository,
    DEFAULT_MIN_VCPU, DEFAULT_MIN_RAM, DEFAULT_MIN_DISK,
)

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img binary is not available')
@pytest.mark.asyncio
async def test_image_repository_list(image_repository: ImageRepository):
    images = await image_repository.list()
    assert len(images) == 0

@pytest.mark.asyncio
async def test_image_repository_get_unknown(image_repository: ImageRepository):
    with pytest.raises(EntityNotFoundException, match='\[404\] No such entity could be found'):
        await image_repository.get_by_uid(uuid.uuid4())

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img binary is not available')
@pytest.mark.asyncio
async def test_image_create(home: pathlib.Path,
                            image_mock_server: pytest_httpserver.HTTPServer,
                            image_repository: ImageRepository):
    image_path = home.joinpath('images').joinpath('mock.qcow2')
    image = Image(name='Test Image',
                url=image_mock_server.url_for('/image.img'),
                path=image_path)
    assert image.dirty
    await image.save()
    assert not image.dirty
    assert image_path.exists()
    assert image_path.is_file()
    assert image_path.stat().st_size > 0
    assert image.url == image_mock_server.url_for('/image.img')
    assert image.path == image_path
    assert image.min_vcpu == DEFAULT_MIN_VCPU
    assert image.min_ram == DEFAULT_MIN_RAM
    assert image.min_disk == DEFAULT_MIN_DISK
    loaded = await image_repository.get_by_uid(image.uid, reload=True)
    assert loaded == image
    assert not image.dirty
    assert len(await image_repository.list()) == 1
    await image_repository.remove(image)
    assert len(await image_repository.list()) == 0

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img binary is not available')
@pytest.mark.asyncio
async def test_image_create_duplicate_raises(image_seed: Image,
                                             image_mock_server: pytest_httpserver.HTTPServer):
    with pytest.raises(EntityInvariantException, match=f'\[400\] Image at {image_seed.path} already exists'):
        duplicate = Image(name='Duplicate Image',
                          url=image_mock_server.url_for('/image.img'),
                          path=image_seed.path)
        await duplicate.save()

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img binary is not available')
@pytest.mark.asyncio
async def test_image_modify(image_seed: Image,
                            image_mock_server: pytest_httpserver,
                            image_repository: ImageRepository):
    assert len(await image_repository.list()) == 1
    assert await image_repository.get_by_uid(image_seed.uid) == image_seed
    assert image_seed.url == image_mock_server.url_for('/image.img')
    assert image_seed.path is not None
    assert image_seed.min_vcpu == DEFAULT_MIN_VCPU
    assert image_seed.min_ram == DEFAULT_MIN_RAM
    assert image_seed.min_disk == DEFAULT_MIN_DISK

    image_seed.min_vcpu = 2
    image_seed.min_ram = BinarySizedValue(2, BinaryScale.G)
    image_seed.min_disk = BinarySizedValue(10, BinaryScale.G)
    assert image_seed.dirty == True
    await image_seed.save()
    assert await image_repository.get_by_uid(image_seed.uid) == image_seed
    assert len(await image_repository.list()) == 1

    loaded = await image_repository.get_by_uid(image_seed.uid, reload=True)
    assert loaded == image_seed

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img binary is not available')
@pytest.mark.asyncio
async def test_image_remove(image_seed: Image,
                            image_repository: ImageRepository):
    assert len(await image_repository.list()) == 1
    await image_repository.remove(image_seed)
    assert len(await image_repository.list()) == 0
    with pytest.raises(EntityNotFoundException, match=f'\[404\] No such entity could be found'):
        await image_repository.remove(image_seed)
