import typing
import sqlalchemy

from kaso_mashin import KasoMashinException
from kaso_mashin.server.controllers import AbstractController
from kaso_mashin.common.model import IdentityKind, IdentityModel


class IdentityController(AbstractController):
    """
    An identity controller
    """

    def list(self) -> typing.List[IdentityModel]:
        return list(self.db.session.scalars(sqlalchemy.select(IdentityModel)).all())

    def get(self, identity_id: int | None = None, name: str | None = None) -> IdentityModel | None:
        """
        Return an identity by either its id or name

        Args:
            identity_id: An optional identity id
            name: An optional network name

        Returns:
            The IdentityModel matching the search parameters or None if not found
        Raises:
            KasoMashinException: When neither identity_id nor name are provided
        """
        if not identity_id and not name:
            raise KasoMashinException(status=400, msg='Neither identity_id nor name are provided')
        if identity_id:
            identity = self.db.session.get(IdentityModel, identity_id)
        else:
            identity = self.db.session.scalar(sqlalchemy.sql.select(IdentityModel).where(IdentityModel.name == name))
        return identity or None

    def create(self, model: IdentityModel) -> IdentityModel:
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def modify(self, identity_id: int, update: IdentityModel) -> IdentityModel:
        current = self.db.session.get(IdentityModel, identity_id)
        if not current:
            raise KasoMashinException(status=404, msg='The identity could not be found')
        if current.kind == IdentityKind.PUBKEY and update.passwd:
            raise KasoMashinException(status=400, msg='Identities of the public key kind cannot have a password')
        if current.kind == IdentityKind.PASSWORD and update.pubkey:
            raise KasoMashinException(status=400, msg='Identities of the password kind cannot have a public key')
        if update.gecos:
            current.gecos = update.gecos
        if update.homedir:
            current.homedir = update.homedir
        if update.shell:
            current.shell = update.shell
        if update.pubkey:
            current.pubkey = update.pubkey
        if update.passwd:
            current.passwd = update.passwd
        self.db.session.add(current)
        self.db.session.commit()
        return current

    def remove(self, identity_id: int):
        # TODO: Should check whether it's in use somewhere
        identity = self.db.session.get(IdentityModel, identity_id)
        if not identity:
            # The identity is not around, should cause a 410
            return True
        self.db.session.delete(identity)
        self.db.session.commit()
        return False
