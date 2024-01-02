import pathlib
from kaso_mashin.common.applied import (
    BinaryScale, BinarySizedValue,
    ImageRepository, ImageEntity, ImageModel,
    DiskRepository, DiskEntity, DiskModel)


def test_applied_disks(applied_session):
    repo = DiskRepository(DiskModel, applied_session)
    disk = DiskEntity.create('Test Disk',
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
        disk.remove()
        repo.remove(disk.id)
        assert repo.get_by_id(disk.id) is None
        assert not disk.path.exists()


def test_applied_disks_from_image(applied_session):
    repo = DiskRepository(DiskModel, applied_session)
    image = ImageEntity(name='jammy', path=pathlib.Path('/Users/imfeldma/var/kaso/images/jammy.qcow2'))
    disk = DiskEntity.create_from_image('Test Disk',
                                        path=pathlib.Path(__file__).parent / 'build' / 'test.qcow2',
                                        size=BinarySizedValue(1, BinaryScale.G),
                                        image=image)
    try:
        repo.create(disk)
        disk.resize(BinarySizedValue(2, BinaryScale.G))
        repo.modify(disk)
    finally:
        disk.remove()
        assert not disk.path.exists()


def test_applied_images(applied_session):
    repo = ImageRepository(ImageModel, applied_session)
    image = ImageEntity(name='Test Image',
                        path=pathlib.Path(__file__),
                        min_vcpu=2,
                        min_ram=BinarySizedValue(2, BinaryScale.G),
                        min_disk=BinarySizedValue(1, BinaryScale.G))
    try:
        repo.create(image)
        loaded = repo.get_by_id(image.id)
        assert image == loaded
        image.min_vcpu = 99
        image.min_ram = BinarySizedValue(99, BinaryScale.T)
        image.min_disk = BinarySizedValue(99, BinaryScale.T)
        updated = repo.modify(image)
        assert image == updated
        listed = repo.list()
        assert len(listed) == 1
        assert image == listed[0]
    finally:
        repo.remove(image.id)
        assert repo.get_by_id(image.id) is None
