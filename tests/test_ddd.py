import pathlib
from kaso_mashin.common.ddd import (
    Repository, SizedValue, BinaryScale,
    ImageModel, ImageEntity,
    InstanceModel, InstanceEntity,
    DiskModel, DiskEntity )


def test_instance_entity(ddd_session):
    repo = Repository[InstanceModel](model=InstanceModel, session=ddd_session)
    instance = InstanceEntity(name='Test Entity')
    try:
        repo.create(InstanceModel.from_aggregateroot(instance))
        model = repo.get_by_id(instance.id)
        loaded = model.as_entity()
        assert loaded == instance
    finally:
        repo.remove(instance.id)
        assert repo.get_by_id(instance.id) is None


def test_image_entity(ddd_session):
    repo = Repository[ImageModel](model=ImageModel, session=ddd_session)
    image = ImageEntity(name='Test Entity')
    try:
        repo.create(ImageModel.from_aggregateroot(image))
        model = repo.get_by_id(image.id)
        loaded = model.as_entity()
        assert loaded == image
    finally:
        repo.remove(image.id)
        assert repo.get_by_id(image.id) is None


def test_disk_entity(ddd_session):
    repo = Repository[DiskModel](model=DiskModel, session=ddd_session)
    disk = DiskEntity(name='Test Entity', path=pathlib.Path(__file__), size=SizedValue(value=1, scale=BinaryScale.GB))
    try:
        repo.create(DiskModel.from_aggregateroot(disk))
        model = repo.get_by_id(disk.id)
        loaded = model.as_entity()
        assert loaded == disk
    finally:
        repo.remove(disk.id)
        assert repo.get_by_id(disk.id) is None
