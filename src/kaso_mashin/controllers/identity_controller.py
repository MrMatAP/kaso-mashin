import typing
import sqlalchemy

from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import IdentityModel


class IdentityController(AbstractController):
    """
    An identity controller
    """

    def list(self) -> typing.List[IdentityModel]:
        with self.db.session() as s:
            identities = s.scalars(sqlalchemy.select(IdentityModel)).all()
        return identities

    def get(self, identity_id: int) -> IdentityModel:
        with self.db.session() as s:
            return s.get(IdentityModel, identity_id)

    def create(self, model: IdentityModel) -> IdentityModel:
        with self.db.session() as s:
            s.add(model)
            s.commit()
        return model

    def remove(self, identity_id: int):
        with self.db.session() as s:
            identity = s.get(IdentityModel, identity_id)
            s.delete(identity)
            s.commit()
