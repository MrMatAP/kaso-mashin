import pytest

import uuid

from kaso_mashin.common import (
    EntityNotFoundException,
    Bootstrap, BootstrapRepository, BootstrapKind
)


@pytest.mark.asyncio
async def test_bootstrap_repository_list(bootstrap_repository: BootstrapRepository):
    bootstraps = await bootstrap_repository.list()
    assert len(bootstraps) == 0

@pytest.mark.asyncio
async def test_bootstrap_repository_get_unknown(bootstrap_repository: BootstrapRepository):
    with pytest.raises(EntityNotFoundException, match='\[404\] No such entity could be found'):
        await bootstrap_repository.get_by_uid(uuid.uuid4())

@pytest.mark.asyncio
async def test_bootstrap_create(bootstrap_repository: BootstrapRepository):
    bootstrap = Bootstrap(name='Test',
                          kind=BootstrapKind.IGNITION,
                          content='''
                          version: 1.0.0
                          variant: flatcar
                          files:
                          - path: /etc/hostname
                            mode: 0644
                            overwrite: true
                            contents:
                              inline: |
                                {{ name }}
                          ''')
    assert bootstrap.dirty
    await bootstrap.save()
    assert not bootstrap.dirty
    assert len(bootstrap.required_keys) == 1
    assert 'name' in bootstrap.required_keys
    loaded = await bootstrap_repository.get_by_uid(bootstrap.uid, reload = True)
    assert loaded == bootstrap
    assert not loaded.dirty
    assert len(await bootstrap_repository.list()) == 1
    await bootstrap_repository.remove(bootstrap)
    assert len(await bootstrap_repository.list()) == 0
