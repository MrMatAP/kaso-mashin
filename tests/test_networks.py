import uuid
import ipaddress

import pytest
from conftest import seed, BaseTest

from kaso_mashin.common import UniqueIdentifier, EntityNotFoundException
from kaso_mashin.common.entities import (
    NetworkModel,
    NetworkEntity,
    NetworkListSchema,
    NetworkListEntrySchema,
    NetworkGetSchema,
    NetworkModifySchema,
    DEFAULT_HOST_NETWORK_NAME,
    DEFAULT_BRIDGED_NETWORK_NAME,
    DEFAULT_SHARED_NETWORK_NAME,
)


@pytest.mark.asyncio(scope="session")
class TestEmptyNetworks:
    """
    Test behaviour of the Network entities in an entirely empty database
    """

    async def test_list(self, test_context_empty):
        assert 0 == len(await test_context_empty.runtime.identity_repository.list())

    async def test_list_api(self, test_context_empty):
        resp = test_context_empty.client.get("/api/networks/")
        assert 200 == resp.status_code
        schema = NetworkListSchema.model_validate_json(resp.content)
        assert 3 == len(schema.entries), "3 default networks are precreated"

    async def test_get_by_uid(self, test_context_empty):
        with pytest.raises(EntityNotFoundException) as enfe:
            await test_context_empty.runtime.network_repository.get_by_uid(
                str(uuid.uuid4())
            )
        assert 400 == enfe.value.status, "Exception status is 400"
        assert "No such entity" == enfe.value.msg, "Exception status no such entity"


@pytest.mark.asyncio(scope="session")
class TestSeededNetworks(BaseTest[NetworkModel, NetworkEntity, NetworkGetSchema]):

    def assert_list_by_model(
        self, obj: NetworkListEntrySchema | NetworkEntity, model: NetworkModel
    ):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name
        assert obj.kind == model.kind
        assert obj.cidr == ipaddress.IPv4Network(model.cidr)

    def assert_get_by_model(
        self, obj: NetworkGetSchema | NetworkEntity, model: NetworkModel
    ):
        assert obj.uid == UniqueIdentifier(model.uid)
        assert obj.name == model.name
        assert obj.kind == model.kind
        assert obj.cidr == ipaddress.IPv4Network(model.cidr)
        assert obj.gateway == ipaddress.IPv4Address(model.gateway)
        assert obj.dhcp_start == ipaddress.IPv4Address(model.dhcp_start)
        assert obj.dhcp_end == ipaddress.IPv4Address(model.dhcp_end)

    async def test_list(self, test_context_seeded):
        entities = await test_context_seeded.runtime.network_repository.list()
        assert len(seed["networks"]) + 3 == len(entities)
        for entity in entities:
            assert isinstance(entity, NetworkEntity)
            if entity.name in [
                DEFAULT_BRIDGED_NETWORK_NAME,
                DEFAULT_SHARED_NETWORK_NAME,
                DEFAULT_HOST_NETWORK_NAME,
            ]:
                continue
            model = BaseTest.find_match_in_seeds(entity.uid, seed["networks"])
            self.assert_list_by_model(entity, model)

    async def test_list_api(self, test_context_seeded):
        resp = test_context_seeded.client.get("/api/networks/")
        assert 200 == resp.status_code
        schema = NetworkListSchema.model_validate_json(resp.content)
        assert len(seed.get("networks")) + 3 == len(schema.entries)
        for entry in schema.entries:
            if entry.name in [
                DEFAULT_BRIDGED_NETWORK_NAME,
                DEFAULT_SHARED_NETWORK_NAME,
                DEFAULT_HOST_NETWORK_NAME,
            ]:
                continue
            model = self.find_match_in_seeds(entry.uid, seed["networks"])
            self.assert_list_by_model(entry, model)

    @pytest.mark.parametrize("network", seed.get("networks", []))
    async def test_get(self, test_context_seeded, network):
        entity = await test_context_seeded.runtime.network_repository.get_by_uid(
            network.uid
        )
        assert isinstance(entity, NetworkEntity)
        self.assert_get_by_model(entity, network)

    @pytest.mark.parametrize("network", seed.get("networks", []))
    async def test_get_api(self, test_context_seeded, network):
        resp = test_context_seeded.client.get(f"/api/networks/{network.uid}")
        assert 200 == resp.status_code
        schema = NetworkGetSchema.model_validate(resp.json())
        model = self.find_match_in_seeds(schema.uid, seed["networks"])
        self.assert_get_by_model(schema, model)

    @pytest.mark.parametrize("network", seed.get("networks", []))
    async def test_modify(self, test_context_seeded, network):
        entity = await test_context_seeded.runtime.network_repository.get_by_uid(
            network.uid
        )
        mod = NetworkModifySchema(name=f"{entity.name} - Modified")
        await entity.modify(mod)
