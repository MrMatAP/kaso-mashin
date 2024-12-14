import uuid
import ipaddress

import pytest

import kaso_mashin
import kaso_mashin.base
import kaso_mashin.domain


@pytest.mark.asyncio
async def test_network_repository_list(network_repository: kaso_mashin.domain.NetworkRepository):
    await network_repository.list()
    assert True     # No exception

@pytest.mark.asyncio
async def test_network_repository_get_unknown(network_repository: kaso_mashin.domain.NetworkRepository):
    with pytest.raises(kaso_mashin.base.EntityNotFoundException, match='\[404\] No such entity could be found'):
        await network_repository.get_by_uid(uuid.uuid4())

@pytest.mark.asyncio
async def test_network_create(network_repository: kaso_mashin.domain.NetworkRepository):
    current_networks = len(await network_repository.list())
    net = kaso_mashin.domain.Network(name='Test Network',
                  kind=kaso_mashin.domain.NetworkKind.VMNET_HOST,
                  cidr=ipaddress.IPv4Network('10.0.0.0/24'),
                  gateway=ipaddress.IPv4Address('10.0.0.1'))
    assert net.dhcp_start == ipaddress.IPv4Address('10.0.0.2')
    assert net.dhcp_end == ipaddress.IPv4Address('10.0.0.254')
    assert net.dirty
    await net.save()
    assert not net.dirty
    loaded = await network_repository.get_by_uid(net.uid, reload=True)
    assert loaded == net
    assert not loaded.dirty
    assert len(await network_repository.list()) == current_networks + 1
    await network_repository.remove(net)
    assert len(await network_repository.list()) == current_networks

@pytest.mark.asyncio
async def test_network_create_duplicate_raises(network_seed: kaso_mashin.domain.Network,
                                               network_repository: kaso_mashin.domain.NetworkRepository):
    with pytest.raises(kaso_mashin.base.EntityInvariantException, match=f'\[400\] Network {network_seed.name} already uses CIDR {network_seed.cidr}'):
        duplicate = kaso_mashin.domain.Network(name='Duplicate Network',
                            kind=kaso_mashin.domain.NetworkKind.VMNET_HOST,
                            cidr=network_seed.cidr,
                            gateway=network_seed.gateway)
        await duplicate.save()
