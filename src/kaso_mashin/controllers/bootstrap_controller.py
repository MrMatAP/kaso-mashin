import shutil
import pathlib

from kaso_mashin import KasoMashinException
from kaso_mashin.executor import execute
from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import BootstrapKind, InstanceModel, CIVendorData, CIUserData, CIMetaData, CINetworkConfig


class BootstrapController(AbstractController):
    """
    A bootstrap controller
    """

    def bootstrap(self, model: InstanceModel):
        match model.bootstrapper:
            case BootstrapKind.CI.value:
                self.cloud_init(model=model)
            case BootstrapKind.CI_DISK.value:
                self.cloud_init(model=model)
                self.create_ci_image(model=model)
            case BootstrapKind.IGNITION.value:
                self.ignition(model=model)
            case BootstrapKind.NONE.value:
                return
            case _:
                raise KasoMashinException(status=400, msg=f'There is no bootstrapper {model.bootstrapper}')

    def cloud_init(self, model: InstanceModel):
        ci_base_path = pathlib.Path(model.path).joinpath('cloud-init')
        ci_base_path.mkdir(parents=True, exist_ok=True)
        vendordata = CIVendorData()
        vendordata.render_to(ci_base_path.joinpath('vendor-data'))
        metadata = CIMetaData(instance_id=f'instance_{model.instance_id}', hostname=model.name)
        metadata.render_to(ci_base_path.joinpath('meta-data'))
        userdata = CIUserData(phone_home_url=f'http://{model.network.host_ip4}:{model.network.host_phone_home_port}/'
                                             f'$INSTANCE_ID',
                              pubkey=model.identity.credentials)
        userdata.render_to(ci_base_path.joinpath('user-data'))
        if model.static_ip4:
            networkconfig = CINetworkConfig(mac=model.mac,
                                            ip4=model.static_ip4,
                                            nm4=model.network.nm4,
                                            gw4=model.network.gw4,
                                            ns4=model.network.ns4)
            networkconfig.render_to(ci_base_path.joinpath('network-config'))

    def ignition(self, model: InstanceModel):
        ign_base_path = pathlib.Path(model.path).joinpath('ignition')
        ign_base_path.mkdir(parents=True, exist_ok=True)
        raise KasoMashinException(status=500, msg='Ignition bootstrapper is not yet implemented')

    def create_ci_image(self, model: InstanceModel):
        ci_base_path = pathlib.Path(model.path).joinpath('cloud-init')
        ci_base_path.mkdir(parents=True, exist_ok=True)
        execute('dd', ['if=/dev/zero', f'of={model.ci_disk_path}', 'bs=512', 'count=2880'])
        hdiutil_output = execute('hdiutil', ['attach', '-nomount', model.ci_disk_path])
        kernel_device = hdiutil_output.stdout.strip()
        execute('diskutil', ['eraseVolume', 'MS-DOS', 'CIDATA', kernel_device])
        shutil.copytree(ci_base_path, '/Volumes/CIDATA', dirs_exist_ok=True)
        execute('diskutil', ['eject', kernel_device])