import pathlib
import configparser

from mrmat_playground import console, PlaygroundException
from mrmat_playground.executor import execute
from mrmat_playground.cloud_init import Metadata, UserData, VendorData, NetworkConfig

class Instance:
    """
    Abstraction of a VM instance
    """

    def __init__(self, config: configparser.ConfigParser, instance_id: str, name: str, backing_disk_path: pathlib.Path):
        self._instance_id = instance_id
        self._name = name
        self._backing_disk_path = backing_disk_path
        if not backing_disk_path.exists():
            raise PlaygroundException(status=400, msg=f'Backing disk path at {backing_disk_path} does not exist')

        self._path = pathlib.Path(config['DEFAULT']['playground_path'], 'instances', name)
        self._os_disk_path = pathlib.Path(self._path, 'os.qcow2')
        self._os_disk_size = config['DEFAULT']['default_os_disk_size'] or '5G'
        self._cloud_init_path = pathlib.Path(self._path, 'cloud-init.img')
        self._bin_path = pathlib.Path(self._path, 'vm.sh')
        self._inventory_path = pathlib.Path(self._path, 'inventory.yaml')
        self._playbook_path = pathlib.Path(self._path, 'deploy.yaml')
        self._pubkey = config['DEFAULT']['default_pubkey']


    @property
    def instance_id(self):
        return self._instance_id

    @property
    def name(self):
        return self._name

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def backing_disk_path(self) -> pathlib.Path:
        return self._backing_disk_path

    @property
    def os_disk_path(self) -> pathlib.Path:
        return self._os_disk_path

    @property
    def os_disk_size(self) -> str:
        return self._os_disk_size

    @os_disk_size.setter
    def os_disk_size(self, value: str):
        self._os_disk_size = value

    @property
    def cloud_init_path(self) -> pathlib.Path:
        return self._cloud_init_path

    @property
    def bin_path(self) -> pathlib.Path:
        return self._bin_path

    @property
    def inventory_path(self) -> pathlib.Path:
        return self._inventory_path

    @property
    def playbook_path(self) -> pathlib.Path:
        return self._playbook_path

    @property
    def pubkey(self) -> str:
        return self._pubkey

    @pubkey.setter
    def pubkey(self, value: str):
        self._pubkey = value

    def create(self):
        self._path.mkdir(parents=True, exist_ok=True)
        if not self._os_disk_path.exists():
            execute('qemu-img',
                    ['create', '-f', 'qcow2', '-b', self.backing_disk_path, '-F', 'qcow2', self.os_disk_path])
            console.log(f'Created OS disk at {self.os_disk_path} from backing store {self.backing_disk_path}')
            execute('qemu-img', ['resize', self.os_disk_path, self.os_disk_size])
            console.log(f'Resized OS disk at {self.os_disk_path} to {self.os_disk_size}')
        if not self.cloud_init_path.exists():
            execute('dd', ['if=/dev/zero', f'of={self.cloud_init_path}', 'bs=512', 'count=2880'])
            hdiutil_output = execute('hdiutil', ['attach', '-nomount', self.cloud_init_path])
            kernel_device = hdiutil_output.stdout.strip()
            execute('diskutil', ['eraseVolume', 'MS-DOS', 'CIDATA', kernel_device])
            with open('/Volumes/CIDATA/meta-data', mode='w', encoding='UTF-8') as m:
                m.write(Metadata(instance_id=self.instance_id, hostname=self.name).render())
            with open('/Volumes/CIDATA/user-data', mode='w', encoding='UTF-8') as u:
                u.write(UserData(pubkey=self.pubkey).render())
            with open('/Volumes/CIDATA/vendor-data', mode='w', encoding='UTF-8') as v:
                v.write(VendorData().render())
            with open('/Volumes/CIDATA/network-config', mode='w', encoding='UTF-8') as n:
                n.write(NetworkConfig(mac='00:00:5e:00:52:02', ip='172.16.3.5/24', gw='172.16.3.1',
                                      ns='172.16.3.1').render())
            execute('diskutil', ['eject', kernel_device])
            console.log(f'Created cloud-init disk image at {self.cloud_init_path}')

    def remove(self):
        pass
