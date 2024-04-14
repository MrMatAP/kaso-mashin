import pathlib
import uuid

import pytest
from conftest import seed, BaseTest

from kaso_mashin.common import UniqueIdentifier, EntityNotFoundException
from kaso_mashin.common.entities import (
    IdentityModel,
    IdentityEntity,
    IdentityListSchema,
    IdentityListEntrySchema,
    IdentityGetSchema,
    IdentityModifySchema,
)


@pytest.mark.asyncio(scope="session")
class TestEmptyEntityIdentities:
    """
    Test behaviour of the Identity entities in an entirely empty database
    """

    async def test_list(self, test_context_empty):
        assert 0 == len(await test_context_empty.runtime.identity_repository.list())

    async def test_list_api(self, test_context_empty):
        resp = test_context_empty.client.get("/api/identities/")
        assert 200 == resp.status_code
        schema = IdentityListSchema.model_validate_json(resp.content)
        assert [] == schema.entries

    async def test_get_by_uid(self, test_context_empty):
        with pytest.raises(EntityNotFoundException) as enfe:
            await test_context_empty.runtime.identity_repository.get_by_uid(
                uuid.uuid4()
            )
        assert 400 == enfe.value.status, "Exception status is 400"
        assert "No such entity" == enfe.value.msg, "Exception status no such entity"

    # @pytest.mark.parametrize('identity', seed.get('identities', []))
    # async def test_create(self, test_context_empty, identity):
    #     entity = None
    #     try:
    #         entity = await IdentityEntity.create(name=identity.name,
    #                                              kind=identity.kind,
    #                                              gecos=identity.gecos,
    #                                              homedir=pathlib.Path(identity.homedir),
    #                                              shell=identity.shell,
    #                                              credential=identity.credential)
    #         assert entity.uid is not None
    #         assert entity.name == identity.name
    #         assert entity.kind == identity.kind
    #         assert entity.gecos == identity.gecos
    #         assert entity.homedir == pathlib.Path(identity.homedir)
    #         assert entity.shell == identity.shell
    #         assert entity.credential == identity.credential
    #     finally:
    #         assert entity is not None, 'We have created the identity'
    #         await test_context_empty.runtime.identity_repository.remove(entity.uid)
    #         with pytest.raises(EntityNotFoundException):
    #             await test_context_empty.runtime.identity_repository.get_by_uid(entity.uid)


@pytest.mark.asyncio(scope="session")
class TestSeededIdentities(BaseTest[IdentityModel, IdentityEntity, IdentityGetSchema]):
    """
    Test behaviour of Identity entities in a seeded database
    """

    def assert_list_by_model(
        self, obj: IdentityListEntrySchema | IdentityEntity, model: IdentityModel
    ):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name
        assert obj.kind == model.kind
        assert obj.gecos == model.gecos

    def assert_get_by_model(
        self, obj: IdentityGetSchema | IdentityEntity, model: IdentityModel
    ):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name
        assert obj.kind == model.kind
        assert obj.gecos == model.gecos
        assert obj.homedir == pathlib.Path(model.homedir)
        assert obj.shell == model.shell
        assert obj.credential == model.credential

    async def test_list(self, test_context_seeded):
        entities = await test_context_seeded.runtime.identity_repository.list()
        assert len(entities) == len(seed["identities"])
        for entity in entities:
            assert isinstance(entity, IdentityEntity)
            model = BaseTest.find_match_in_seeds(entity.uid, seed["identities"])
            self.assert_list_by_model(entity, model)

    async def test_list_api(self, test_context_seeded):
        resp = test_context_seeded.client.get("/api/identities/")
        assert 200 == resp.status_code
        schema = IdentityListSchema.model_validate_json(resp.content)
        assert len(seed.get("identities")) == len(schema.entries)
        for entry in schema.entries:
            model = self.find_match_in_seeds(entry.uid, seed["identities"])
            self.assert_list_by_model(entry, model)

    @pytest.mark.parametrize("identity", seed.get("identities", []))
    async def test_get(self, test_context_seeded, identity):
        entity = await test_context_seeded.runtime.identity_repository.get_by_uid(
            identity.uid
        )
        assert isinstance(entity, IdentityEntity)
        self.assert_get_by_model(entity, identity)

    @pytest.mark.parametrize("identity", seed.get("identities", []))
    async def test_get_api(self, test_context_seeded, identity):
        resp = test_context_seeded.client.get(f"/api/identities/{identity.uid}")
        assert 200 == resp.status_code
        schema = IdentityGetSchema.model_validate(resp.json())
        model = self.find_match_in_seeds(schema.uid, seed["identities"])
        self.assert_get_by_model(schema, model)

    @pytest.mark.parametrize("identity", seed.get("identities", []))
    async def test_modify(self, test_context_seeded, identity):
        entity = await test_context_seeded.runtime.identity_repository.get_by_uid(
            identity.uid
        )
        mod = IdentityModifySchema(name=f"{entity.name} - Modified")
        await entity.modify(mod)
