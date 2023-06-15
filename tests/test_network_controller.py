import pytest

from kaso_mashin.controllers import NetworkController

from conftest import test_networks


@pytest.mark.parametrize('test_network', test_networks)
def test_network_create(test_db, test_network):
    network_controller = NetworkController(config=test_db.config, db=test_db)
    persisted = network_controller.create(test_network)
    assert persisted.network_id
    assert persisted.name == test_network.name
    assert persisted.host_ip4 == test_network.host_ip4
    assert persisted.nm4 == test_network.nm4
    assert persisted.gw4 == test_network.gw4
    assert persisted.ns4 == test_network.ns4
    assert persisted.host_phone_home_port == test_network.host_phone_home_port


# def test_network_remove(test_db):
#     network_controller = NetworkController(config=test_db.config, db=test_db)
#     assert len(network_controller.list()) == 0
#     for network in test_networks:
#         network_controller.create(network)
#     assert len(network_controller.list()) == len(test_networks)
#     for network in test_networks:
#         network_controller.remove(network)
#     assert len(network_controller.list()) == 0


