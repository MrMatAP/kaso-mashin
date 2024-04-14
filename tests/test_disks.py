import pathlib
import uuid

import pytest
from conftest import seed, BaseTest

from kaso_mashin.common import (
    UniqueIdentifier, EntityNotFoundException, BinarySizedValue, BinaryScale )
from kaso_mashin.common.entities import (
    DiskModel, DiskEntity,
    DiskListSchema, DiskListEntrySchema, DiskGetSchema, DiskModifySchema, DiskFormat)


@pytest.mark.asyncio(scope='session')
class TestEmptyDisks:
    """
    Test behaviour of empty Disk entities in an entirely empty database
    """

    async def test_list(self, test_context_empty):
        assert 0 == len(await test_context_empty.runtime.disk_repository.list())

    async def test_list_api(self, test_context_empty):
        resp = test_context_empty.client.get('/api/disks/')
        assert 200 == resp.status_code
        schema = DiskListSchema.model_validate_json(resp.content)
        assert [] == schema.entries

    async def test_get_by_uid(self, test_context_empty):
        with pytest.raises(EntityNotFoundException) as enfe:
            await test_context_empty.runtime.disk_repository.get_by_uid(uuid.uuid4())
        assert 400 == enfe.value.status, 'Exception status is 400'
        assert 'No such entity' == enfe.value.msg, 'Exception status no such entity'


@pytest.mark.asyncio(scope='session')
class TestSeededDisks(BaseTest[DiskModel, DiskEntity, DiskGetSchema]):
    """
    Test behaviour of Identity entities in a seeded database
    """

    def assert_list_by_model(self, obj: DiskListEntrySchema | DiskEntity, model: DiskModel):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name

    def assert_get_by_model(self, obj: DiskGetSchema | DiskEntity, model: DiskModel):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.path == pathlib.Path(model.path)
        assert obj.size.value == model.size
        assert obj.size.scale == model.size_scale
        assert obj.disk_format == model.disk_format
        if isinstance(obj, DiskGetSchema) and obj.image_uid is None:
            assert obj.image_uid == model.image_uid
        elif isinstance(obj, DiskEntity) and obj.image is None:
            assert obj.image == model.image_uid
        else:
            assert obj.image.uid == model.image_uid

    async def test_list(self, test_context_seeded):
        entities = await test_context_seeded.runtime.disk_repository.list()
        assert len(entities) == len(seed['disks'])
        for entity in entities:
            assert isinstance(entity, DiskEntity)
            model = BaseTest.find_match_in_seeds(entity.uid, seed['disks'])
            self.assert_list_by_model(entity, model)

    async def test_list_api(self, test_context_seeded):
        resp = test_context_seeded.client.get('/api/disks/')
        assert 200 == resp.status_code
        schema = DiskListSchema.model_validate_json(resp.content)
        assert len(seed.get('disks')) == len(schema.entries)
        for entry in schema.entries:
            model = self.find_match_in_seeds(entry.uid, seed['disks'])
            self.assert_list_by_model(entry, model)

    @pytest.mark.parametrize('disk', seed.get('disks', []))
    async def test_get(self, test_context_seeded, disk):
        entity = await test_context_seeded.runtime.disk_repository.get_by_uid(disk.uid)
        assert isinstance(entity, DiskEntity)
        self.assert_get_by_model(entity, disk)

    @pytest.mark.parametrize('disk', seed.get('disks', []))
    async def test_get_api(self, test_context_seeded, disk):
        resp = test_context_seeded.client.get(f'/api/disks/{disk.uid}')
        assert 200 == resp.status_code
        schema = DiskGetSchema.model_validate(resp.json())
        model = self.find_match_in_seeds(schema.uid, seed['disks'])
        self.assert_get_by_model(schema, model)

    async def test_modify(self, test_context_seeded):
        entity = None
        try:
            entity = await DiskEntity.create(name='Local test disk',
                                             path=test_context_seeded.config.path / 'test.raw',
                                             size=BinarySizedValue(1, BinaryScale.M),
                                             disk_format=DiskFormat.Raw)
            assert entity.uid is not None
            mod = DiskModifySchema(size=BinarySizedValue(value=2, scale=BinaryScale.M))
            await entity.modify(mod)
            assert entity.size == BinarySizedValue(2, BinaryScale.M)
        finally:
            if entity is not None:
                await entity.remove()
