import pytest
import pathlib

from kaso_mashin.common.generics.base_types import BinaryScale, BinarySizedValue
from kaso_mashin.common.generics.disks import DiskEntity, DiskModel, DiskAggregateRoot, AsyncDiskAggregateRoot


def test_disks(generics_session_maker):
    aggregate_root = DiskAggregateRoot(model=DiskModel, session_maker=generics_session_maker)

    assert aggregate_root.list() == []
    try:
        disk = aggregate_root.create(DiskEntity(name='Test Disk',
                                                path=pathlib.Path(__file__).parent / 'build' / 'test.qcow2',
                                                size=BinarySizedValue(1, BinaryScale.G)))
        loaded = aggregate_root.get(disk.id)
        assert disk == loaded
        disk.size = BinarySizedValue(2, scale=BinaryScale.G)
        updated = aggregate_root.modify(disk)
        assert disk == updated
        listed = aggregate_root.list()
        assert len(listed) == 1
        assert disk == listed[0]
    finally:
        aggregate_root.remove(disk.id)
        assert len(aggregate_root.list()) == 0
        assert not disk.path.exists()


@pytest.mark.asyncio(scope='module')
async def test_async_disks(generics_async_session_maker):
    aggregate_root = AsyncDiskAggregateRoot(model=DiskModel, session_maker=generics_async_session_maker)
    try:
        disk = await aggregate_root.create(DiskEntity(name='Test Disk',
                                                      path=pathlib.Path(__file__).parent / 'build' / 'test.qcow2',
                                                      size=BinarySizedValue(1, BinaryScale.G)))
        loaded = await aggregate_root.get(disk.id)
        assert disk == loaded
        disk.size = BinarySizedValue(2, scale=BinaryScale.G)
        updated = await aggregate_root.modify(disk)
        assert disk == updated
        listed = await aggregate_root.list()
        assert len(listed) == 1
        assert disk == listed[0]
    finally:
        await aggregate_root.remove(disk.id)
        assert len(await aggregate_root.list()) == 0
        assert not disk.path.exists()

# def test_applied_disks_from_image(applied_session):
#     repo = DiskRepository(DiskModel, applied_session)
#     image = ImageEntity(name='jammy', path=pathlib.Path('/Users/imfeldma/var/kaso/images/jammy.qcow2'))
#     disk = DiskEntity.create_from_image('Test Disk',
#                                         path=pathlib.Path(__file__).parent / 'build' / 'test.qcow2',
#                                         size=BinarySizedValue(1, BinaryScale.G),
#                                         image=image)
#     try:
#         repo.create(disk)
#         disk.resize(BinarySizedValue(2, BinaryScale.G))
#         repo.modify(disk)
#     finally:
#         disk.remove()
#         assert not disk.path.exists()

#
# def test_applied_images(applied_session):
#     repo = ImageRepository(ImageModel, applied_session)
#     image = ImageEntity(name='Test Image',
#                         path=pathlib.Path(__file__),
#                         min_vcpu=2,
#                         min_ram=BinarySizedValue(2, BinaryScale.G),
#                         min_disk=BinarySizedValue(1, BinaryScale.G))
#     try:
#         repo.create(image)
#         loaded = repo.get_by_id(image.id)
#         assert image == loaded
#         image.min_vcpu = 99
#         image.min_ram = BinarySizedValue(99, BinaryScale.T)
#         image.min_disk = BinarySizedValue(99, BinaryScale.T)
#         updated = repo.modify(image)
#         assert image == updated
#         listed = repo.list()
#         assert len(listed) == 1
#         assert image == listed[0]
#     finally:
#         repo.remove(image.id)
#         assert repo.get_by_id(image.id) is None
