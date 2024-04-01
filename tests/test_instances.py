import uuid
import pathlib

import pytest
from conftest import seed, BaseTest


from kaso_mashin.common import (
    UniqueIdentifier, EntityNotFoundException,
    T_Entity, T_EntityModel,
    T_EntityGetSchema, T_EntityListSchema)
from kaso_mashin.common.entities import (
    InstanceModel, InstanceEntity,
    InstanceListSchema, InstanceGetSchema, InstanceModifySchema)


@pytest.mark.asyncio(scope='session')
class TestEmptyInstances:
    """
    Test behaviour of the Instance entities in an entirely empty database
    """

    async def test_list(self, test_context_empty):
        assert 0 == len(await test_context_empty.runtime.instance_repository.list())

    async def test_list_api(self, test_context_empty):
        resp = test_context_empty.client.get('/api/instances/')
        assert 200 == resp.status_code
        assert 0 == len(resp.json())

    async def test_get_by_uid(self, test_context_empty):
        with pytest.raises(EntityNotFoundException) as enfe:
            await test_context_empty.runtime.instance_repository.get_by_uid(str(uuid.uuid4()))
        assert 400 == enfe.value.status, 'Exception status is 400'
        assert 'No such entity' == enfe.value.msg, 'Exception status no such entity'


@pytest.mark.asyncio(scope='session')
class TestSeededInstances(BaseTest[InstanceModel, InstanceEntity, InstanceGetSchema]):

    def assert_list_by_model(self, obj: T_EntityListSchema | T_Entity, model: T_EntityModel):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name

    def assert_get_by_model(self, obj: T_EntityGetSchema | T_Entity, model: T_EntityModel):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name
        assert obj.path == pathlib.Path(model.path)
        assert obj.vcpu == obj.vcpu
        assert obj.ram.value == obj.ram
        assert obj.ram.scale == obj.ram_scale
        assert obj.mac == obj.mac
        # TODO: os_disk and network
