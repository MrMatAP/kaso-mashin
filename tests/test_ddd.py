import uuid
import sqlalchemy.orm

from kaso_mashin.common.ddd import InstanceModel, ImageModel, InstanceRepository


def test_model(ddd_session: sqlalchemy.orm.Session):
    assert ddd_session is not None
    for i in range(0, 16):
        instance_identifier = str(uuid.uuid4())
        ddd_session.add(InstanceModel(id=instance_identifier,
                                      name=f"instance-{instance_identifier}",
                                      vcpu=i,
                                      ram=i))
        image_identifier = str(uuid.uuid4())
        ddd_session.add(ImageModel(id=image_identifier,
                                   name=f"image-{image_identifier}"))
    ddd_session.commit()


def test_repositories(ddd_session: sqlalchemy.orm.Session):
    instance_repository = InstanceRepository(model=InstanceModel, session=ddd_session)
    instances = instance_repository.list()
    assert instances is not None


def test_instance_model_roundtrip(ddd_session: sqlalchemy.orm):
    test_id = str(uuid.uuid4())
    instance = InstanceModel(id=test_id, name=f'instance-{test_id}', vcpu=16, ram=32)
    repository = InstanceRepository(model=InstanceModel, session=ddd_session)
    assert instance == repository.create(instance)
    assert instance == repository.get_by_id(test_id)
    instance.name = f'instance-{test_id}-updated'
    instance.vcpu = 8
    instance.ram = 16
    assert instance == repository.modify(instance)

