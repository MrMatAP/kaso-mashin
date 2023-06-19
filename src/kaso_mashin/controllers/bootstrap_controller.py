import shutil
import pathlib

from kaso_mashin import KasoMashinException
from kaso_mashin.executor import execute
from kaso_mashin.controllers import AbstractController
from kaso_mashin.model import BootstrapKind, InstanceModel, CIVendorData, CIUserData, CIMetadata, CINetworkConfig


class BootstrapController(AbstractController):
    """
    A bootstrap controller
    """

    def bootstrap(self, model: InstanceModel):
        ci_path = pathlib.Path(model.path).joinpath('cloud-init')
        ci_path.mkdir(parents=True, exist_ok=True)
        match model.bootstrapper:
            case BootstrapKind.CI:
                self.cloud_init(model=model, ci_path=ci_path)
            case BootstrapKind.CI_STATIC:
                self.cloud_init(model=model, ci_path=ci_path)
                self.cloud_init_static(model=model, ci_path=ci_path)
                self.create_ci_image(model=model, ci_path=ci_path)
            case BootstrapKind.IGNITION:
                self.ignition(model=model, ci_path=ci_path)
            case BootstrapKind.NONE:
                return
            case _:
                raise KasoMashinException(status=400, msg=f'There is no bootstrapper {model.bootstrapper}')

    def cloud_init(self, model: InstanceModel, ci_path: pathlib.Path):
        vendordata = CIVendorData()
        vendordata.render_to(ci_path.joinpath('vendor-data'))
        metadata = CIMetadata(instance_id=f'instance_{model.instance_id}', hostname=model.name)
        metadata.render_to(ci_path.joinpath('meta-data'))
        userdata = CIUserData(phone_home_url=f'http://{model.network.host_ip4}:{model.network.host_phone_home_port}/'
                                             f'$INSTANCE_ID',
                              pubkey=model.identity.public_key)
        userdata.render_to(ci_path.joinpath('user-data'))

    def cloud_init_static(self, model: InstanceModel, ci_path: pathlib.Path):
        if not model.static_ip4:
            raise KasoMashinException(status=400, msg='There is no static IP4 address registered for this instance')
        networkconfig = CINetworkConfig(mac=model.mac,
                                        ip4=model.static_ip4,
                                        nm4=model.network.nm4,
                                        gw4=model.network.gw4,
                                        ns4=model.network.ns4)
        networkconfig.render_to(ci_path.joinpath('network-config'))

    def ignition(self, model: InstanceModel, ci_path: pathlib.Path):
        pass

    def create_ci_image(self, model: InstanceModel, ci_path: pathlib.Path):
        execute('dd', ['if=/dev/zero', f'of={model.ci_disk_path}', 'bs=512', 'count=2880'])
        hdiutil_output = execute('hdiutil', ['attach', '-nomount', model.ci_disk_path])
        kernel_device = hdiutil_output.stdout.strip()
        execute('diskutil', ['eraseVolume', 'MS-DOS', 'CIDATA', kernel_device])
        shutil.copytree(ci_path, '/Volumes/CIDATA', dirs_exist_ok=True)
        execute('diskutil', ['eject', kernel_device])
