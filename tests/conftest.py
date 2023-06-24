import pytest

from kaso_mashin.config import Config
from kaso_mashin.db import DB
from kaso_mashin.model import NetworkKind, NetworkModel

test_networks = [
    NetworkModel(name='test-network-0',
                 kind=NetworkKind.VMNET_HOST,
                 host_ip4='172.16.100.10',
                 nm4='255.255.255.0',
                 gw4='172.16.100.1',
                 ns4='172.16.100.1',
                 host_phone_home_port=10200),
    NetworkModel(name='test-network-1',
                 kind=NetworkKind.VMNET_SHARED,
                 host_ip4='172.16.101.10',
                 nm4='255.255.255.0',
                 gw4='172.16.101.1',
                 ns4='8.8.8.8',
                 host_phone_home_port=8000)
]


@pytest.fixture
def test_config(tmp_path):
    config_file = tmp_path.joinpath('.kaso')
    with config_file.open('w', encoding='UTF-8') as c:
        c.write(f'path: {tmp_path}')
    return Config(config_file=config_file)


@pytest.fixture
def test_db(test_config):
    return DB(config=test_config)
