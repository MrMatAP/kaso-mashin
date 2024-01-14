import pytest
import pathlib

from kaso_mashin.common.base_types import BinaryScale, BinarySizedValue
from kaso_mashin.common.generics.disks import DiskEntity, DiskModel, DiskAggregateRoot
from kaso_mashin.common.generics.images import ImageEntity, ImageModel, ImageAggregateRoot


@pytest.mark.asyncio
async def test_async_disks(generics_async_session_maker):
    try:
        disk_aggregate_root = DiskAggregateRoot(model=DiskModel, session_maker=generics_async_session_maker)
        disk = await DiskEntity.create(owner=disk_aggregate_root,
                                       name='Test Disk',
                                       path=pathlib.Path(__file__).parent / 'build' / 'test-async-disks.qcow2',
                                       size=BinarySizedValue(1, BinaryScale.M))

        loaded = await disk_aggregate_root.get(disk.uid)
        assert disk == loaded
        await disk.resize(BinarySizedValue(2, scale=BinaryScale.M))
        updated = await disk_aggregate_root.get(disk.uid, force_reload=True)
        assert disk.size == updated.size
        assert disk == updated
        listed = await disk_aggregate_root.list()
        assert len(listed) == 1
        assert disk == listed[0]
    finally:
        await disk.remove()
        assert len(await disk_aggregate_root.list()) == 0
        assert not disk.path.exists()


@pytest.mark.asyncio
async def test_async_images(generics_async_session_maker):
    try:
        image_aggregate_root = ImageAggregateRoot(model=ImageModel, session_maker=generics_async_session_maker)
        image = await ImageEntity.create(owner=image_aggregate_root,
                                         name='Test Image',
                                         path=pathlib.Path(__file__).parent / 'build' / 'test-async-images.qcow2')
        loaded = await image_aggregate_root.get(image.uid)
        assert image == loaded
        await image.set_min_vcpu(10)
        await image.set_min_ram(BinarySizedValue(2, BinaryScale.G))
        await image.set_min_disk(BinarySizedValue(10, BinaryScale.G))
        # await image.create_os_disk(path=pathlib.Path(__file__).parent / 'build' / 'os.qcow2',
        #                            size=BinarySizedValue(10, BinaryScale.M))
        updated = await image_aggregate_root.get(image.uid)
        assert image == updated
        listed = await image_aggregate_root.list()
        assert len(listed) == 1
        assert image == listed[0]
    finally:
        await image.remove()
        assert len(await image_aggregate_root.list()) == 0
        assert not image.path.exists()
