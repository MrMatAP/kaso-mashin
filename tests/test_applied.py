import pathlib
from kaso_mashin.common.applied import (
    BinaryScale, BinarySizedValue,
    ImageRepository, ImageEntity, ImageModel,
    DiskRepository, DiskEntity, DiskModel)


def test_applied_disks(applied_session):
    repo = DiskRepository(DiskModel, applied_session)
    disk = DiskEntity(name="Test Disk",
                      path=pathlib.Path(__file__),
                      size=BinarySizedValue(value=1, scale=BinaryScale.GB))
    try:
        repo.create(disk)
        loaded = repo.get_by_id(disk.id)
        assert disk == loaded
        disk.size = BinarySizedValue(2, scale=BinaryScale.GB)
        updated = repo.modify(disk)
        assert disk == updated
        listed = repo.list()
        assert len(listed) == 1
        assert disk == listed[0]
    finally:
        repo.remove(disk.id)
        assert repo.get_by_id(disk.id) is None


def test_applied_images(applied_session):
    repo = ImageRepository(ImageModel, applied_session)
    image = ImageEntity(name='Test Image',
                        path=pathlib.Path(__file__),
                        min_vcpu=2,
                        min_ram=BinarySizedValue(2, BinaryScale.GB),
                        min_disk=BinarySizedValue(1, BinaryScale.GB))
    try:
        repo.create(image)
        loaded = repo.get_by_id(image.id)
        assert image == loaded
        image.min_vcpu = 99
        image.min_ram = BinarySizedValue(99, BinaryScale.TB)
        image.min_disk = BinarySizedValue(99, BinaryScale.TB)
        updated = repo.modify(image)
        assert image == updated
        listed = repo.list()
        assert len(listed) == 1
        assert image == listed[0]
    finally:
        repo.remove(image.id)
        assert repo.get_by_id(image.id) is None
