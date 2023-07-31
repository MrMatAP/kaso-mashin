import shutil
import typing
import sqlalchemy

from kaso_mashin import KasoMashinException
from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import InstanceModel, VMScriptModel, TaskSchema


class InstanceController(AbstractController):
    """
    An instance controller
    """

    def __init__(self, runtime: 'Runtime'):
        super().__init__(runtime)
        self.config.path.joinpath('instances').mkdir(parents=True, exist_ok=True)

    def list(self) -> typing.List[InstanceModel]:
        return list(self.db.session.scalars(sqlalchemy.select(InstanceModel)).all())

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

    def create(self, model: InstanceModel, task: TaskSchema) -> InstanceModel:
        model.path = self.config.path.joinpath('instances').joinpath(model.name)
        if model.path.exists():
            raise KasoMashinException(status=400,
                                      msg=f'Instance path at {model.path} already exists',
                                      task=task)
        model.os_disk_path = model.path.joinpath('os.qcow2')
        model.ci_base_path = model.path.joinpath('cloud-init')
        model.ci_disk_path = model.path.joinpath('ci.img')
        model.vm_script_path = model.path.joinpath('vm.sh')
        task.progress(1, f'Calculated instance path at {model.path}')

        identities = [self.identity_controller.get(i.identity_id) for i in model.identities]
        model.identities = identities
        task.progress(2, 'Resolved all provided identities')

        self.db.session.add(model)
        self.db.session.commit()
        task.progress(3, f'Registered instance with ID {model.instance_id}')

        # We start with 00:00:5e, then simply add the instance_id integer
        mac_raw = str(hex(int(0x5056000000) + model.instance_id)).removeprefix('0x').zfill(12)
        model.mac = f'{mac_raw[0:2]}:{mac_raw[2:4]}:{mac_raw[4:6]}:{mac_raw[6:8]}:{mac_raw[8:10]}:{mac_raw[10:12]}'
        self.db.session.add(model)
        self.db.session.commit()
        task.progress(4, f'Calculated MAC address {model.mac}')

        model.path.mkdir(parents=True, exist_ok=True)
        task.progress(5, f'Created instance path {model.path}')

        self.os_disk_controller.create(model.os_disk_path, model.image.path)
        task.progress(6, 'Created OS disk')

        self.bootstrap_controller.create(model)
        task.progress(7, 'Created bootstrap')

        vm_script = VMScriptModel(model=model)
        with open(model.vm_script_path, mode='w', encoding='UTF-8') as v:
            v.write(vm_script.render())
        model.vm_script_path.chmod(0o755)
        task.progress(8, 'Created VM script')

        #     status.update(f'Start the instance using "sudo {vm_script_path} now')
        #     if model.network.kind == NetworkKind.VMNET_SHARED:
        #         status.update('Waiting for the instance to phone home')
        #         self.phonehome_controller.wait_for_instance(model=model)
        #         status.update('Instance phoned home')

        task.success(msg='Instance created')
        return model

    def modify(self, instance_id: int, update: InstanceModel) -> InstanceModel | None:
        instance = self.db.session.get(InstanceModel, instance_id)
        instance.name = update.name
        # TODO
        self.db.session.add(instance)
        self.db.session.commit()
        return instance

    def remove(self, instance_id: int) -> bool:
        instance = self.db.session.get(InstanceModel, instance_id)
        if not instance:
            # The instance is not around, should cause a 410
            return True
        shutil.rmtree(instance.path)
        self.db.session.delete(instance)
        self.db.session.commit()
        return False
