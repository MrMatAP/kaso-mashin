import typing
import pathlib
import sqlalchemy

from kaso_mashin import KasoMashinException
from kaso_mashin.config import Config
from kaso_mashin.controllers import AbstractController
from kaso_mashin.db import DB
from kaso_mashin.model import InstanceModel


class InstanceController(AbstractController):
    """
    An instance controller
    """

    def __init__(self, config: Config, db: DB):
        super().__init__(config, db)
        config.path.joinpath('instances').mkdir(parents=True, exist_ok=True)

    def list(self) -> typing.List[InstanceModel]:
        """
        List existing instances
        Returns:
            A list of instance models
        """
        return self.db.session.scalars(sqlalchemy.select(InstanceModel)).all()

    def get(self, instance_id: typing.Optional[int] = None, name: typing.Optional[str] = None) -> InstanceModel | None:
        """
        Get an existing instance by id or name
        Args:
            instance_id: An instance id
            name: An instance name

        Returns:
            An instance model
        Raises:
            KasoMashinException: When neither instance_id nor name is specified
        """
        if not instance_id and not name:
            raise KasoMashinException(status=400, msg='One of instance_id or name is required')
        if instance_id:
            return self.db.session.get(InstanceModel, instance_id)
        return self.db.session.scalar(
            sqlalchemy.sql.select(InstanceModel).where(InstanceModel.name == name))

    def create(self, model: InstanceModel) -> InstanceModel:
        """
        Create an instance
        Args:
            model: the instance model template

        Returns:
            An instantiated instance model
        """
        self.db.session.add(model)
        self.db.session.commit()
        # We start with 00:00:5e, then simply add the instance_id integer
        mac_raw = str(hex(int(0x5056000000) + model.instance_id)).removeprefix('0x').zfill(12)
        model.mac = f'{mac_raw[0:2]}:{mac_raw[2:4]}:{mac_raw[4:6]}:{mac_raw[6:8]}:{mac_raw[8:10]}:{mac_raw[10:12]}'
        self.db.session.add(model)
        self.db.session.commit()
        instance_path = pathlib.Path(model.path)
        instance_path.mkdir(parents=True, exist_ok=True)
        return model

    def modify(self, instance_id: int, update: InstanceModel) -> InstanceModel | None:
        instance = self.db.session.get(InstanceModel, instance_id)
        instance.name = update.name
        # TODO
        self.db.session.add(instance)
        self.db.session.commit()
        return instance

    def remove(self, instance_id: int):
        instance = self.db.session.get(InstanceModel, instance_id)
        self.db.session.delete(instance)
        self.db.session.commit()
