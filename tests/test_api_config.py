from kaso_mashin.common.config import ConfigSchema


class TestConfigAPI:
    """
    Test the behaviour of the Config API
    """

    def test_api_config_get(self, test_kaso_context_empty):
        resp = test_kaso_context_empty.client.get('/api/config/')
        assert resp.status_code == 200
        c = ConfigSchema.model_validate_json(resp.content)
        assert c.version is not None
        assert len(c.predefined_images) > 0
