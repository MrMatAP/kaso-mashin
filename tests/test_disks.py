import pytest

import kaso_mashin.base
from conftest import qemu_img_available, disk_repository

import pathlib
import uuid

import kaso_mashin
import kaso_mashin.domain


@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img binary is not available')
@pytest.mark.asyncio
async def test_disk_repository_list(disk_repository: kaso_mashin.domain.DiskRepository):
    disks = await disk_repository.list()
    assert len(disks) == 0

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_repository_get_unknown(disk_repository: kaso_mashin.domain.DiskRepository):
    with pytest.raises(kaso_mashin.base.EntityNotFoundException, match='\[404\] No such entity could be found'):
        await disk_repository.get_by_uid(uuid.uuid4())

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_create(home: pathlib.Path, disk_repository: kaso_mashin.domain.DiskRepository):
    disk_path = home.joinpath('disks').joinpath('disk.qcow2')
    disk = kaso_mashin.domain.Disk(name='Mock Disk',
                path=disk_path,
                size=kaso_mashin.base.BinarySizedValue(1, kaso_mashin.base.BinaryScale.M),
                disk_format=kaso_mashin.domain.DiskFormat.QCoW2)
    assert disk.dirty
    await disk.save()
    assert not disk.dirty
    assert disk_path.exists()
    assert disk_path.is_file()
    assert disk_path.stat().st_size > 0
    assert disk.path == disk_path
    assert disk.size == kaso_mashin.base.BinarySizedValue(1, kaso_mashin.base.BinaryScale.M)
    assert len(await disk_repository.list()) == 1
    loaded = await disk_repository.get_by_uid(disk.uid, reload=True)
    assert disk == loaded
    assert len(await disk_repository.list()) == 1
    await disk_repository.remove(disk)
    assert len(await disk_repository.list()) == 0

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_create_from_image(home: pathlib.Path,
                                      image_seed: kaso_mashin.domain.Image,
                                      disk_repository: kaso_mashin.domain.DiskRepository):
    disk_path = home.joinpath('disks').joinpath('disk-from-image.qcow2')
    disk = kaso_mashin.domain.Disk(name='Mock Image Disk',
                path=disk_path,
                size=kaso_mashin.base.BinarySizedValue(1, kaso_mashin.base.BinaryScale.M),
                disk_format=kaso_mashin.domain.DiskFormat.QCoW2,
                image=image_seed)
    assert disk.dirty
    await disk.save()
    assert not disk.dirty
    assert disk_path.exists()
    assert disk_path.is_file()
    assert disk_path.stat().st_size > 0
    assert disk.path == disk_path
    assert disk.size == kaso_mashin.base.BinarySizedValue(1, kaso_mashin.base.BinaryScale.M)
    assert disk.image == image_seed
    assert disk in image_seed.disks
    loaded = await disk_repository.get_by_uid(disk.uid, reload=True)
    assert loaded == disk
    assert not loaded.dirty
    assert len(await disk_repository.list()) == 1
    await disk_repository.remove(disk)
    assert len(await disk_repository.list()) == 0

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_create_duplicate_raises(disk_seed: kaso_mashin.domain.Disk):
    with pytest.raises(kaso_mashin.base.EntityInvariantException, match=f'\[400\] Disk at {disk_seed.path} already exists'):
        duplicate = kaso_mashin.domain.Disk(name='Duplicate Disk', path=disk_seed.path)
        await duplicate.save()

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_grow(disk_seed: kaso_mashin.domain.Disk,
                         disk_repository: kaso_mashin.domain.DiskRepository):
    assert disk_seed.size == kaso_mashin.base.BinarySizedValue(1, kaso_mashin.base.BinaryScale.M)
    disk_seed.size = kaso_mashin.base.BinarySizedValue(2, kaso_mashin.base.BinaryScale.M)
    assert disk_seed.dirty
    await disk_seed.save()
    assert not disk_seed.dirty
    actual_size = kaso_mashin.base.BinarySizedValue(disk_seed.path.stat().st_size, kaso_mashin.base.BinaryScale.b)
    assert actual_size.at_scale(kaso_mashin.base.BinaryScale.M) == disk_seed.size
    loaded = await disk_repository.get_by_uid(disk_seed.uid, reload=True)
    assert loaded == disk_seed

@pytest.mark.skipif(not qemu_img_available(), reason='qemu-img is not available')
@pytest.mark.asyncio
async def test_disk_shrink(disk_seed: kaso_mashin.domain.Disk,
                           disk_repository: kaso_mashin.domain.DiskRepository):
    assert disk_seed.size == kaso_mashin.base.BinarySizedValue(1, kaso_mashin.base.BinaryScale.M)
    disk_seed.size = kaso_mashin.base.BinarySizedValue(512, kaso_mashin.base.BinaryScale.k)
    await disk_seed.save()
    actual_size = kaso_mashin.base.BinarySizedValue(disk_seed.path.stat().st_size, kaso_mashin.base.BinaryScale.b)
    assert actual_size.at_scale(kaso_mashin.base.BinaryScale.k) == disk_seed.size
    loaded = await disk_repository.get_by_uid(disk_seed.uid, reload=True)
    assert loaded == disk_seed
