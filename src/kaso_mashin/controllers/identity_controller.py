import typing
import sqlalchemy

from kaso_mashin import KasoMashinException
from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import IdentityModel


class IdentityController(AbstractController):
    """
    An identity controller
    """

    def list(self) -> typing.List[IdentityModel]:
        return self.db.session.scalars(sqlalchemy.select(IdentityModel)).all()

    def get(self, identity_id: typing.Optional[int] = None , name: typing.Optional[str] = None) -> IdentityModel | None:
        """
        Return an identity by either id or name
        Args:
            identity_id: The identity id
            name: The network name

        Returns:
            The IdentityModel matching the search parameters or None if not found
        Raises:
            KasoMashinException: When neither identity_id nor name are provided
        """
        if not identity_id and not name:
            raise KasoMashinException(status=400, msg='Neither identity_id nor name are provided')
        if identity_id:
            return self.db.session.get(IdentityModel, identity_id)
        return self.db.session.scalar(
            sqlalchemy.sql.select(IdentityModel).where(IdentityModel.name == name))

    def create(self, model: IdentityModel) -> IdentityModel:
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def remove(self, identity_id: int):
        identity = self.db.session.get(IdentityModel, identity_id)
        self.db.session.delete(identity)
        self.db.session.commit()
