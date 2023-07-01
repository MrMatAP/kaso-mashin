import typing
import sqlalchemy
import sqlalchemy.sql

from kaso_mashin import KasoMashinException
from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import NetworkModel


class NetworkController(AbstractController):
    """
    A network controller
    """

    DEFAULT_HOST_NETWORK_NAME = 'default_host_network'
    DEFAULT_BRIDGED_NETWORK_NAME = 'default_bridged_network'
    DEFAULT_SHARED_NETWORK_NAME = 'default_shared_network'

    def list(self) -> typing.List[NetworkModel]:
        networks = self.db.session.scalars(sqlalchemy.select(NetworkModel)).all()
        return networks

    def get(self,
            network_id: typing.Optional[int]=None,
            name: typing.Optional[str]=None) -> NetworkModel | None:
        """
        Return a network by either id or name
        Args:
            network_id: The network id
            name: The network name

        Returns:
            The NetworkModel matching the search parameters or None if not found
        Raises:
            KasoMashinException: When neither network_id nor name are provided
        """
        if network_id:
            return self.db.session.get(NetworkModel, network_id)
        if name:
            return self.db.session.scalar(
                sqlalchemy.sql.select(NetworkModel).where(NetworkModel.name == name))
        raise KasoMashinException(status=500, msg='Network id or name must be provided')

    def create(self, model: NetworkModel) -> NetworkModel:
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def modify(self, network_id: int, update: NetworkModel) -> NetworkModel:
        network = self.db.session.get(NetworkModel, network_id)
        network.name = update.name
        network.kind = update.kind
        network.host_ip4 = update.host_ip4
        network.nm4 = update.nm4
        network.gw4 = update.gw4
        network.ns4 = update.ns4
        network.host_phone_home_port = update.host_phone_home_port
        network.dhcp_start = update.dhcp_start
        network.dhcp_end = update.dhcp_end
        self.db.session.add(network)
        self.db.session.commit()
        return network

    def remove(self, network_id: int):
        network = self.db.session.get(NetworkModel, network_id)
        self.db.session.delete(network)
        self.db.session.commit()
