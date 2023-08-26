import pytest
from conftest import seed
from kaso_mashin.common.model import (
    ExceptionSchema,
    IdentityKind, IdentityModel,
    IdentityCreateSchema, IdentityModifySchema, IdentitySchema )


class TestEmptyIdentityAPI:
    """
    Test the behaviour of the Identity API in an entirely empty database
    """

    def test_api_identity_empty_list(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.get('/api/identities/')
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_identity_empty_get(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.get('/api/identities/1')
        assert resp.status_code == 404
        ex = ExceptionSchema.model_validate_json(resp.content)
        assert ex.status == 404
        assert ex.msg == 'No such identity could be found'

    def test_api_identity_empty_modify(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.get('/api/identities/1')
        assert resp.status_code == 404
        ex = ExceptionSchema.model_validate_json(resp.content)
        assert ex.status == 404
        assert ex.msg == 'No such identity could be found'

    def test_api_identity_empty_remove(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.delete('/api/identities/1')
        assert resp.status_code == 410
        assert resp.content == b''


class TestEmptyIdentityAPICreative:

    @pytest.mark.parametrize('identity', seed.get('identities', []))
    def test_api_identity_empty_create(self, test_kaso_context_empty, identity):
        identity = IdentityCreateSchema(name=identity.name,
                                        kind=identity.kind,
                                        gecos=identity.gecos,
                                        homedir=identity.homedir,
                                        shell=identity.shell,
                                        passwd=identity.passwd,
                                        pubkey=identity.pubkey)
        resp = test_kaso_context_empty.client.post('/api/identities/',
                                                   json=identity.model_dump())
        assert resp.status_code == 201
        model = IdentitySchema.model_validate_json(resp.content)
        assert model.identity_id
        assert model.name == identity.name
        assert model.kind == identity.kind
        assert model.gecos == identity.gecos
        assert model.homedir == identity.homedir
        assert model.shell == identity.shell
        if model.kind == IdentityKind.PUBKEY:
            assert model.pubkey == identity.pubkey
            assert model.passwd is None
        else:
            assert model.pubkey is None
            assert model.passwd == identity.passwd

    def test_api_identity_fail_empty_passwd(self, test_kaso_context_empty):
        # We might actually want this to fail
        identity = IdentityCreateSchema(name='i-should-fail',
                                        kind=IdentityKind.PASSWORD,
                                        gecos=None,
                                        homedir=None,
                                        shell=None,
                                        passwd='',
                                        pubkey=None)
        resp = test_kaso_context_empty.client.post('/api/identities/',
                                                   json=identity.model_dump())
        assert resp.status_code == 201
        model = IdentitySchema.model_validate_json(resp.content)
        assert model.identity_id
        assert model.passwd == ''


class TestSeededIdentityAPI:
    """
    Test the behaviour of the identity API in a seeded database
    """

    def test_api_identity_seeded_list(self, test_kaso_context_seeded):
        resp = test_kaso_context_seeded.client.get('/api/identities/')
        assert resp.status_code == 200
        identities = resp.json()
        assert len(identities) == len(seed.get('identities', []))

    @pytest.mark.parametrize('identity', seed.get('identities', []))
    def test_api_identity_seeded_get(self, test_kaso_context_seeded, identity):
        # Find the model by its name first to get its id
        resp = test_kaso_context_seeded.client.get(f'/api/identities/?name={identity.name}')
        assert resp.status_code == 200
        model_by_name = IdentitySchema.model_validate_json(resp.content)
        assert model_by_name.identity_id
        assert model_by_name.name == identity.name
        assert model_by_name.kind == identity.kind
        assert model_by_name.gecos == identity.gecos
        assert model_by_name.shell == identity.shell
        assert model_by_name.homedir == identity.homedir
        if model_by_name.kind == IdentityKind.PUBKEY:
            assert model_by_name.pubkey
            assert model_by_name.passwd is None
        else:
            assert model_by_name.pubkey is None
            assert model_by_name.passwd == identity.passwd
        # Now find the model by its id
        resp = test_kaso_context_seeded.client.get(f'/api/identities/{model_by_name.identity_id}')
        assert resp.status_code == 200
        model_by_id = IdentitySchema.model_validate_json(resp.content)
        assert model_by_id == model_by_name

    def test_api_identity_seeded_modify(self, test_kaso_context_seeded):
        resp = test_kaso_context_seeded.client.get('/api/identities/1')
        assert resp.status_code == 200
        n = IdentitySchema.model_validate_json(resp.content)
        n.gecos = 'Modified Gecos'
        # Modify
        mod = IdentityModifySchema(gecos=n.gecos,       # This one will be updated
                                   homedir=n.homedir,
                                   shell=n.shell,
                                   passwd=n.passwd,
                                   pubkey=n.pubkey)
        resp = test_kaso_context_seeded.client.put('/api/identities/1', json=mod.model_dump())
        assert resp.status_code == 200
        u = IdentitySchema.model_validate_json(resp.content)
        assert n == u
        # Get it again
        resp = test_kaso_context_seeded.client.get('/api/identities/1')
        assert resp.status_code == 200
        q = IdentitySchema.model_validate_json(resp.content)
        assert n == q


class TestSeededIdentityAPIDestruction:
    """
    Test the behaviour of the identity API in a seeded database, destroying its entities
    """

    def test_api_identity_seeded_remove(self, test_kaso_context_seeded):
        resp = test_kaso_context_seeded.client.delete(f'/api/identities/1')
        assert resp.status_code == 204
        assert resp.content == b''
        assert test_kaso_context_seeded.runtime.db.session.get(IdentityModel, 1) is None
        resp = test_kaso_context_seeded.client.delete(f'/api/identities/1')
        assert resp.status_code == 410
        assert resp.content == b''


    # def test_api_identity_empty_create(self, test_kaso_context_seeded):
    #     identity = IdentityCreateSchema(name='test',
    #                                     kind=IdentityKind.PUBKEY,
    #                                     gecos='Test Identity',
    #                                     homedir='/home/test',
    #                                     shell='/bin/bash',
    #                                     pubkey='ssh-rsa foo')
    #     resp = test_kaso_context_seeded.client.post('/api/identities/', json=identity.model_dump())
    #     assert resp.status_code == 201
    #     identity = IdentitySchema.model_validate_json(resp.content)
    #     assert identity.name == 'test'
    #     assert identity.kind == IdentityKind.PUBKEY
    #     assert identity.gecos == 'Test Identity'
    #     assert identity.homedir == '/home/test'
    #     assert identity.shell == '/bin/bash'
    #     assert identity.pubkey == 'ssh-rsa foo'
