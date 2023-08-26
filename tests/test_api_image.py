from kaso_mashin.common.model import ExceptionSchema


class TestEmptyImageAPI:
    """
    Test the behaviour of the Image API in an entirely empty database
    """

    def test_api_image_empty_list(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.get('/api/images/')
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_image_empty_get(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.get('/api/images/1')
        assert resp.status_code == 404
        ex = ExceptionSchema.model_validate_json(resp.content)
        assert ex.status == 404
        assert ex.msg == 'No such image could be found'

    def test_api_image_empty_modify(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.get('/api/images/1')
        assert resp.status_code == 404
        ex = ExceptionSchema.model_validate_json(resp.content)
        assert ex.status == 404
        assert ex.msg == 'No such image could be found'

    def test_api_image_empty_remove(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.delete('/api/images/1')
        assert resp.status_code == 410
        assert resp.content == b''


# class TestSeededImageAPI:
#     """
#     Test the behaviour of the image API in a seeded database
#     """
#
#     def test_api_image_seeded_list(self, test_kaso_context_seeded):
#         resp = test_kaso_context_seeded.get('/api/images/')
#         assert resp.status_code == 200
#         identities = resp.json()
#         assert len(identities) == len(seed.get('images', []))
#
