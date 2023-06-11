import typing
import sqlalchemy

from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import NetworkModel


class NetworkController(AbstractController):
    """
    A network controller
    """

    def list(self) -> typing.List[NetworkModel]:
        with self.db.session() as s:
            networks = s.scalars(sqlalchemy.select(NetworkModel)).all()
        return networks

    def get(self, network_id: int) -> NetworkModel:
        with self.db.session() as s:
            return s.get(NetworkModel, network_id)

    def create(self, model: NetworkModel) -> NetworkModel:
        with self.db.session() as s:
            s.add(model)
            s.commit()
        return model

    def modify(self, network_id: int, update: NetworkModel) -> NetworkModel:
        with self.db.session() as s:
            network = s.get(NetworkModel, network_id)
            network.name = update.name
            network.kind = update.kind
            network.host_ip4 = update.host_ip4
            network.nm4 = update.nm4
            network.gw4 = update.gw4
            network.ns4 = update.ns4
            s.add(network)
            s.commit()
        return network

    def remove(self, network_id: int):
        with self.db.session() as s:
            network = s.get(NetworkModel, network_id)
            s.delete(network)
            s.commit()
