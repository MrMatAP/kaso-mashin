import typing
import sqlalchemy

from kaso_mashin import KasoMashinException
from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import InstanceModel, NetworkModel


class InstanceController(AbstractController):
    """
    An instance controller
    """

    def list(self) -> typing.List[InstanceModel]:
        with self.db.session() as s:
            instances = s.scalars(sqlalchemy.select(InstanceModel)).all()
        return instances

    def get(self, instance_id: int) -> InstanceModel:
        with self.db.session() as s:
            return s.get(InstanceModel, instance_id)

    def create(self, model: InstanceModel) -> InstanceModel:

        instance_path = self.config.path.joinpath(model.name)
        if instance_path.exists():
            raise KasoMashinException(status=400, msg='Instance path at {instance_path} already exists')
        model.path = str(instance_path)
        model.os_disk_path = str(instance_path.joinpath('os.qcow2'))

        with self.db.session() as s:
            s.add(model)
            s.commit()
            # We start with 00:00:5e, then simply add the instance_id integer
            mac_raw = str(hex(int(0x5056000000) + model.instance_id)).removeprefix('0x').zfill(12)
            model.mac = f'{mac_raw[0:2]}:{mac_raw[2:4]}:{mac_raw[4:6]}:{mac_raw[6:8]}:{mac_raw[8:10]}:{mac_raw[10:12]}'
            s.add(model)
            s.commit()

        instance_path.mkdir(parents=True, exist_ok=True)
        return model

    def modify(self, instance_id: int, update: InstanceModel) -> InstanceModel:
        with self.db.session() as s:
            instance = s.get(InstanceModel, instance_id)
            instance.name = update.name
            # TODO
            s.add(instance)
            s.commit()
        return instance

    def remove(self, instance_id: int):
        with self.db.session() as s:
            instance = s.get(InstanceModel, instance_id)
            s.delete(instance)
            s.commit()
