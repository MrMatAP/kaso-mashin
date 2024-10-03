import pytest

import pathlib
import uuid

from kaso_mashin.common import (
    EntityNotFoundException,
    Identity, IdentityRepository, IdentityKind
)

@pytest.mark.asyncio
async def test_identity_repository(identity_repository: IdentityRepository):
    identities = await identity_repository.list()
    assert len(identities) == 0

@pytest.mark.asyncio
async def test_identity_repository_get_unknown(identity_repository: IdentityRepository):
    with pytest.raises(EntityNotFoundException, match='\[404\] No such entity could be found'):
        await identity_repository.get_by_uid(uuid.uuid4())

@pytest.mark.asyncio
async def test_identity_create(identity_repository: IdentityRepository):
    identity = Identity(name='Test Identity', kind=IdentityKind.PUBKEY)
    assert identity.dirty
    await identity.save()
    assert not identity.dirty
    loaded = await identity_repository.get_by_uid(identity.uid, reload=True)
    assert loaded == identity
    assert not loaded.dirty
    assert len(await identity_repository.list()) == 1
    await identity_repository.remove(identity)
    assert len(await identity_repository.list()) == 0

@pytest.mark.asyncio
async def test_identity_modify(identity_seed: Identity,
                               identity_repository: IdentityRepository):
    assert len(await identity_repository.list()) == 1
    identity_seed.gecos = 'Modified GECOS'
    identity_seed.homedir = pathlib.Path('/usr/local/home/modified')
    identity_seed.shell = '/bin/zsh'
    identity_seed.credential = 'ssh-rsa some-secret-key'
    assert identity_seed.dirty
    await identity_seed.save()
    assert not identity_seed.dirty
    loaded = await identity_repository.get_by_uid(identity_seed.uid, reload=True)
    assert loaded == identity_seed
