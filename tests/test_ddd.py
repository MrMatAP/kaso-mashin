
from kaso_mashin.common.ddd import Repository, ImageModel, ImageEntity, InstanceModel, InstanceEntity


def test_instance_entity(ddd_session):
    repo = Repository(model=InstanceModel, session=ddd_session)
    instance = InstanceEntity(name='Test Instance')
    try:
        repo.create(InstanceModel.from_aggregateroot(instance))
        model = repo.get_by_id(instance.id)
        loaded = model.as_entity()
        assert loaded == instance
    finally:
        repo.remove(instance.id)
        assert repo.get_by_id(instance.id) is None


def test_image_entity(ddd_session):
    repo = Repository(model=ImageModel, session=ddd_session)
    image = ImageEntity(name='Test Entity')
    try:
        repo.create(ImageModel.from_aggregateroot(image))
        model = repo.get_by_id(image.id)
        loaded = model.as_entity()
        assert loaded == image
    finally:
        repo.remove(image.id)
        assert repo.get_by_id(image.id) is None
