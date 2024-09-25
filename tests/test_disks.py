import pathlib
import uuid

import pytest
from conftest import qemu_img_available

from kaso_mashin.common import (
    EntityNotFoundException, EntityInvariantException,
    BinarySizedValue, BinaryScale,
    Disk, DiskRepository, DiskFormat,
    Image
)


@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img binary is not available')
@pytest.mark.asyncio
async def test_disk_repository_list(disk_repository: DiskRepository):
    disks = await disk_repository.list()
    assert len(disks) == 0

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_repository_get_unknown(disk_repository: DiskRepository):
    with pytest.raises(EntityNotFoundException, match='\[404\] No such entity could be found'):
        await disk_repository.get_by_uid(uuid.uuid4())

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_create(home: pathlib.Path, disk_repository: DiskRepository):
    disk_path = home.joinpath('disks').joinpath('disk.qcow2')
    disk = Disk(name='Mock Disk',
                path=disk_path,
                size=BinarySizedValue(1, BinaryScale.M),
                disk_format=DiskFormat.QCoW2)
    assert disk.dirty
    await disk.save()
    assert not disk.dirty
    assert disk_path.exists()
    assert disk_path.is_file()
    assert disk_path.stat().st_size > 0
    assert disk.path == disk_path
    assert disk.size == BinarySizedValue(1, BinaryScale.M)
    assert len(await disk_repository.list()) == 1
    await disk_repository.remove(disk)
    assert len(await disk_repository.list()) == 0

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_create_from_image(home: pathlib.Path,
                                      image_seed: Image,
                                      disk_repository: DiskRepository):
    disk_path = home.joinpath('disks').joinpath('disk-from-image.qcow2')
    disk = Disk(name='Mock Image Disk',
                path=disk_path,
                size=BinarySizedValue(1, BinaryScale.M),
                disk_format=DiskFormat.QCoW2,
                image=image_seed)
    assert disk.dirty
    await disk.save()
    assert not disk.dirty
    assert disk_path.exists()
    assert disk_path.is_file()
    assert disk_path.stat().st_size > 0
    assert disk.path == disk_path
    assert disk.size == BinarySizedValue(1, BinaryScale.M)
    assert disk.image == image_seed
    assert disk in image_seed.disks

    assert len(await disk_repository.list()) == 1
    await disk_repository.remove(disk)
    assert len(await disk_repository.list()) == 0

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_create_duplicate_raises(disk_seed: Disk):
    with pytest.raises(EntityInvariantException, match=f'\[400\] Disk at {disk_seed.path} already exists'):
        duplicate = Disk(name='Duplicate Disk', path=disk_seed.path)
        await duplicate.save()

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_grow(disk_seed: Disk):
    assert disk_seed.size == BinarySizedValue(1, BinaryScale.M)
    disk_seed.size = BinarySizedValue(2, BinaryScale.M)
    assert disk_seed.dirty
    await disk_seed.save()
    assert not disk_seed.dirty
    actual_size = BinarySizedValue(disk_seed.path.stat().st_size, BinaryScale.b)
    assert actual_size.at_scale(BinaryScale.M) == disk_seed.size

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_shrink(disk_seed: Disk):
    assert disk_seed.size == BinarySizedValue(1, BinaryScale.M)
    disk_seed.size = BinarySizedValue(512, BinaryScale.k)
    await disk_seed.save()
    actual_size = BinarySizedValue(disk_seed.path.stat().st_size, BinaryScale.b)
    assert actual_size.at_scale(BinaryScale.k) == disk_seed.size
