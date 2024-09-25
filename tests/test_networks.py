import uuid
import ipaddress

import pytest

from kaso_mashin.common import (
    EntityNotFoundException, EntityInvariantException,
    Network, NetworkKind, NetworkRepository
)

@pytest.mark.asyncio
async def test_network_repository_list(network_repository: NetworkRepository):
    networks = await network_repository.list()
    assert len(networks) == 0

@pytest.mark.asyncio
async def test_network_repository_get_unknown(network_repository: NetworkRepository):
    with pytest.raises(EntityNotFoundException, match='\[404\] No such entity could be found'):
        await network_repository.get_by_uid(uuid.uuid4())

@pytest.mark.asyncio
async def test_network_create(network_repository: NetworkRepository):
    net = Network(name='Test Network',
                  kind=NetworkKind.VMNET_HOST,
                  cidr=ipaddress.IPv4Network('10.0.0.0/24'),
                  gateway=ipaddress.IPv4Address('10.0.0.1'))
    assert net.dhcp_start == ipaddress.IPv4Address('10.0.0.2')
    assert net.dhcp_end == ipaddress.IPv4Address('10.0.0.254')
    assert net.dirty
    await net.save()
    assert not net.dirty

@pytest.mark.asyncio
async def test_network_create_duplicate_raises(network_seed: Network,
                                               network_repository: NetworkRepository):
    with pytest.raises(EntityInvariantException, match=f'\[400\] Network {network_seed.name} already uses CIDR {network_seed.cidr}'):
        duplicate = Network(name='Duplicate Network',
                            kind=NetworkKind.VMNET_HOST,
                            cidr=network_seed.cidr,
                            gateway=network_seed.gateway)
        await duplicate.save()
