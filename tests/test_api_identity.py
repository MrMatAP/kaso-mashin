import pytest
from conftest import seed
from kaso_mashin.model import ExceptionSchema, IdentityModifySchema, IdentitySchema


class TestEmptyIdentityAPI:
    """
    Test the behaviour of the Identity API in an entirely empty database
    """

    def test_api_identity_empty_list(self, test_api_client_empty):
        resp = test_api_client_empty.get('/api/identities/')
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_identity_empty_get(self, test_api_client_empty):
        resp = test_api_client_empty.get('/api/identities/1')
        assert resp.status_code == 404
        ex = ExceptionSchema.model_validate_json(resp.content)
        assert ex.status == 404
        assert ex.msg == 'No such identity could be found'

    def test_api_identity_empty_modify(self, test_api_client_empty):
        resp = test_api_client_empty.get('/api/identities/1')
        assert resp.status_code == 404
        ex = ExceptionSchema.model_validate_json(resp.content)
        assert ex.status == 404
        assert ex.msg == 'No such identity could be found'

    def test_api_identity_empty_remove(self, test_api_client_empty):
        resp = test_api_client_empty.delete('/api/identities/1')
        assert resp.status_code == 410
        assert resp.content == b''


class TestSeededIdentityAPI:
    """
    Test the behaviour of the identity API in a seeded database
    """

    def test_api_identity_seeded_list(self, test_api_client_seeded):
        resp = test_api_client_seeded.get('/api/identities/')
        assert resp.status_code == 200
        identities = resp.json()
        assert len(identities) == len(seed.get('identities', []))

    @pytest.mark.parametrize('model', seed.get('identities', []))
    def test_api_identity_seeded_get(self, test_api_client_seeded, model):
        # Find the model by its name first to get its id
        resp = test_api_client_seeded.get(f'/api/identities/?name={model.name}')
        assert resp.status_code == 200
        n = IdentitySchema.model_validate_json(resp.content)
        assert n.name == model.name
        assert n.identity_id
        # Now find the model by its id
        resp = test_api_client_seeded.get(f'/api/identities/{n.identity_id}')
        assert resp.status_code == 200
        i = IdentitySchema.model_validate_json(resp.content)
        assert i == n

    def test_api_identity_seeded_modify(self, test_api_client_seeded):
        resp = test_api_client_seeded.get('/api/identities/1')
        assert resp.status_code == 200
        n = IdentitySchema.model_validate_json(resp.content)
        n.gecos = 'Modified Gecos'
        # Modify
        mod = IdentityModifySchema(gecos=n.gecos,       # This one will be updated
                                   homedir=n.homedir,
                                   shell=n.shell,
                                   passwd=n.passwd,
                                   pubkey=n.pubkey)
        resp = test_api_client_seeded.put('/api/identities/1', json=mod.model_dump())
        assert resp.status_code == 200
        u = IdentitySchema.model_validate_json(resp.content)
        assert n == u
        # Get it again
        resp = test_api_client_seeded.get('/api/identities/1')
        assert resp.status_code == 200
        q = IdentitySchema.model_validate_json(resp.content)
        assert n == q

    def test_api_identity_seeded_remove(self, test_api_client_seeded):
        resp = test_api_client_seeded.delete('/api/identities/1')
        assert resp.status_code == 204
        assert resp.content == b''


    # def test_api_identity_empty_create(self, test_api_client):
    #     identity = IdentityCreateSchema(name='test',
    #                                     kind=IdentityKind.PUBKEY,
    #                                     gecos='Test Identity',
    #                                     homedir='/home/test',
    #                                     shell='/bin/bash',
    #                                     pubkey='ssh-rsa foo')
    #     resp = test_api_client.post('/api/identities/', json=identity.model_dump())
    #     assert resp.status_code == 201
    #     identity = IdentitySchema.model_validate_json(resp.content)
    #     assert identity.name == 'test'
    #     assert identity.kind == IdentityKind.PUBKEY
    #     assert identity.gecos == 'Test Identity'
    #     assert identity.homedir == '/home/test'
    #     assert identity.shell == '/bin/bash'
    #     assert identity.pubkey == 'ssh-rsa foo'
