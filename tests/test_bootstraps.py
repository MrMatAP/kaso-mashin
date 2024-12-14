import pytest

import uuid

import kaso_mashin
import kaso_mashin.base
import kaso_mashin.domain


@pytest.mark.asyncio
async def test_bootstrap_repository_list(bootstrap_repository: kaso_mashin.domain.BootstrapRepository):
    await bootstrap_repository.list()
    assert True     # No exception

@pytest.mark.asyncio
async def test_bootstrap_repository_get_unknown(bootstrap_repository: kaso_mashin.domain.BootstrapRepository):
    with pytest.raises(kaso_mashin.base.EntityNotFoundException, match='\[404\] No such entity could be found'):
        await bootstrap_repository.get_by_uid(uuid.uuid4())

@pytest.mark.asyncio
async def test_bootstrap_create(bootstrap_repository: kaso_mashin.domain.BootstrapRepository):
    starting_bootstraps = len(await kaso_mashin.domain.Bootstrap.repository.list())
    bootstrap = kaso_mashin.domain.Bootstrap(name='Test',
                          kind=kaso_mashin.domain.BootstrapKind.IGNITION,
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
    assert len(await bootstrap_repository.list()) == starting_bootstraps + 1
    await bootstrap_repository.remove(bootstrap)
    assert len(await bootstrap_repository.list()) == starting_bootstraps
