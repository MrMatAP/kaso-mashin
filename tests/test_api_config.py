import pytest

from kaso_mashin.model import ConfigSchema


class TestConfigAPI:
    """
    Test the behaviour of the Config API
    """

    def test_api_config_get(self, test_api_client_empty):
        resp = test_api_client_empty.get('/api/config')
        assert resp.status_code == 200
        c = ConfigSchema.model_validate_json(resp.content)
        assert c.version is not None
        assert len(c.predefined_images) > 0
