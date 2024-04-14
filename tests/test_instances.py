import uuid
import pathlib

import pytest
from conftest import seed, BaseTest


from kaso_mashin.common import UniqueIdentifier, EntityNotFoundException
from kaso_mashin.common.entities import (
    InstanceModel,
    InstanceEntity,
    InstanceListSchema,
    InstanceListEntrySchema,
    InstanceGetSchema,
    InstanceModifySchema,
)


@pytest.mark.asyncio(scope="session")
class TestEmptyInstances:
    """
    Test behaviour of the Instance entities in an entirely empty database
    """

    async def test_list(self, test_context_empty):
        assert 0 == len(await test_context_empty.runtime.instance_repository.list())

    async def test_list_api(self, test_context_empty):
        resp = test_context_empty.client.get("/api/instances/")
        assert 200 == resp.status_code
        schema = InstanceListSchema.model_validate_json(resp.content)
        assert [] == schema.entries

    async def test_get_by_uid(self, test_context_empty):
        with pytest.raises(EntityNotFoundException) as enfe:
            await test_context_empty.runtime.instance_repository.get_by_uid(
                str(uuid.uuid4())
            )
        assert 400 == enfe.value.status, "Exception status is 400"
        assert "No such entity" == enfe.value.msg, "Exception status no such entity"


@pytest.mark.asyncio(scope="session")
class TestSeededInstances(BaseTest[InstanceModel, InstanceEntity, InstanceGetSchema]):

    def assert_list_by_model(
        self, obj: InstanceListEntrySchema | InstanceEntity, model: InstanceModel
    ):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name

    def assert_get_by_model(
        self, obj: InstanceGetSchema | InstanceEntity, model: InstanceModel
    ):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name
        assert obj.path == pathlib.Path(model.path)
        assert obj.vcpu == model.vcpu
        assert obj.ram.value == model.ram
        assert obj.ram.scale == model.ram_scale
        assert obj.mac == model.mac
        # TODO: os_disk and network
        assert obj.bootstrap_file == pathlib.Path(model.bootstrap_file)
