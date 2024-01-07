import pytest
import uuid
import pathlib

from kaso_mashin.common.generics.base_types import BinaryScale, BinarySizedValue
from kaso_mashin.common.generics.repository import Repository
from kaso_mashin.common.generics.async_repository import AsyncRepository
from kaso_mashin.common.generics.disks import DiskEntity, DiskModel


def test_disks(generics_session_maker):
    repo = Repository[DiskEntity](aggregate_root_clazz=DiskEntity,
                                  model_clazz=DiskModel,
                                  session_maker=generics_session_maker)
    # TODO: We need to find a way to default the UUID
    disk = DiskEntity(id=uuid.uuid4(),
                      name='Test Disk',
                      path=pathlib.Path(__file__).parent / 'build' / 'test.qcow2',
                      size=BinarySizedValue(1, BinaryScale.G))
    try:
        repo.create(disk)
        loaded = repo.get_by_id(disk.id)
        assert disk == loaded
        disk.size = BinarySizedValue(2, scale=BinaryScale.G)
        updated = repo.modify(disk)
        assert disk == updated
        listed = repo.list()
        assert len(listed) == 1
        assert disk == listed[0]
    finally:
        repo.remove(disk.id)
        assert len(repo.list()) == 0
        assert not disk.path.exists()


@pytest.mark.asyncio(scope='module')
async def test_async_disks(generics_async_session_maker):
    repo = AsyncRepository[DiskEntity](aggregate_root_clazz=DiskEntity,
                                       model_clazz=DiskModel,
                                       session_maker=generics_async_session_maker)
    # TODO: We need to find a way to default the UUID
    disk = DiskEntity(id=uuid.uuid4(),
                      name='Test Disk',
                      path=pathlib.Path(__file__).parent / 'build' / 'test.qcow2',
                      size=BinarySizedValue(1, BinaryScale.G))
    try:
        await repo.create(disk)
        loaded = await repo.get_by_id(disk.id)
        assert disk == loaded
        disk.size = BinarySizedValue(2, scale=BinaryScale.G)
        updated = await repo.modify(disk)
        assert disk == updated
        listed = await repo.list()
        assert len(listed) == 1
        assert disk == listed[0]
    finally:
        await repo.remove(disk.id)
        assert len(await repo.list()) == 0
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
