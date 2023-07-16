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
            network_id: int | None = None,
            name: str | None = None) -> NetworkModel | None:
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
        if not network_id and not name:
            raise KasoMashinException(status=400, msg='Neither network_id nor name are provided')
        if network_id:
            network = self.db.session.get(NetworkModel, network_id)
        else:
            network = self.db.session.scalar(sqlalchemy.sql.select(NetworkModel).where(NetworkModel.name == name))
        return network or None

    def create(self, model: NetworkModel) -> NetworkModel:
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def modify(self, network_id: int, update: NetworkModel) -> NetworkModel:
        current = self.db.session.get(NetworkModel, network_id)
        if not current:
            raise KasoMashinException(status=404, msg='The network could not be found')
        if update.ns4:
            current.ns4 = update.ns4
        if update.dhcp4_start:
            current.dhcp4_start = update.dhcp4_start
        if update.dhcp4_end:
            current.dhcp_end = update.dhcp4_end
        if update.host_phone_home_port:
            current.host_phone_home_port = update.host_phone_home_port
        self.db.session.add(current)
        self.db.session.commit()
        return current

    def remove(self, network_id: int):
        network = self.db.session.get(NetworkModel, network_id)
        self.db.session.delete(network)
        self.db.session.commit()
