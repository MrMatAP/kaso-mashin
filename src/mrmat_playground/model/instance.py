import os
import pathlib
import shutil

import rich.panel

from mrmat_playground import console, PlaygroundException
from mrmat_playground.executor import execute
from mrmat_playground.model import VMScript, AnsibleInventory, AnsibleCfg, AnsiblePlaybook
from mrmat_playground.model.cloud_init import CIMetadata, CINetworkConfig, CIUserData, CIVendorData


class Instance:
    """
    Abstraction of a VM instance
    """

    def __init__(self, path: pathlib.Path, name: str):
        self._name = name

        self._path = path
        self._instance_id = None
        self._backing_disk_path = None
        self._os_disk_path = pathlib.Path(self._path, 'os.qcow2')
        self._os_disk_size = None
        self._public_key = None
        self._vcpu = 2
        self._ram = 2048
        self._mac = None
        self._metadata = None
        self._userdata = None
        self._vendordata = None
        self._network_config = None
        self._vm_script = None
        self._ansible_inventory = None
        self._ansible_cfg = None

        self._ci_path = pathlib.Path(self._path, 'cloud-init')
        self._ci_img_path = pathlib.Path(self._path, 'cloud-init.img')
        self._vm_script_path = pathlib.Path(self._path, 'vm.sh')
        self._ansible_inventory_path = pathlib.Path(self._path, 'inventory.yaml')
        self._ansible_cfg_path = pathlib.Path(self._path, 'ansible.cfg')
        self._ansible_playbook_path = pathlib.Path(self._path, 'deploy.yaml')
        self._ansible_playbook = AnsiblePlaybook()

    @property
    def instance_id(self):
        return self._instance_id

    @instance_id.setter
    def instance_id(self, value: str):
        if self._instance_id:
            raise PlaygroundException(status=400, msg='The instance_id may not be changed once set')
        self._instance_id = value

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def name(self):
        return self._name

    @property
    def backing_disk_path(self) -> pathlib.Path:
        return self._backing_disk_path

    @backing_disk_path.setter
    def backing_disk_path(self, value: pathlib.Path):
        if self._backing_disk_path:
            raise PlaygroundException(status=400, msg='The backing disk path of an existing instance cannot be changed')
        if not value.exists():
            raise PlaygroundException(status=400, msg=f'Backing disk path at {value} does not exist')
        self._backing_disk_path = value

    @property
    def os_disk_size(self) -> str:
        return self._os_disk_size

    @os_disk_size.setter
    def os_disk_size(self, value: str):
        self._os_disk_size = value

    @property
    def public_key(self) -> str:
        return self._public_key

    @public_key.setter
    def public_key(self, value: str):
        self._public_key = value

    @property
    def vcpu(self):
        return self._vcpu

    @vcpu.setter
    def vcpu(self, value: int):
        self._vcpu = value

    @property
    def ram(self):
        return self._ram

    @ram.setter
    def ram(self, value: int):
        self._ram = value

    @property
    def mac(self):
        return self._mac

    @mac.setter
    def mac(self, value: str):
        if self._mac:
            raise PlaygroundException(status=400, msg='The MAC address may not be changed once set')
        self._mac = value

    @property
    def metadata(self) -> CIMetadata:
        return self._metadata

    @metadata.setter
    def metadata(self, value: CIMetadata):
        self._metadata = value

    @property
    def userdata(self) -> CIUserData:
        return self._userdata

    @userdata.setter
    def userdata(self, value: CIUserData):
        self._userdata = value

    @property
    def vendordata(self) -> CIVendorData:
        return self._vendordata

    @vendordata.setter
    def vendordata(self, value: CIVendorData):
        self._vendordata = value

    @property
    def network_config(self) -> CINetworkConfig:
        return self._network_config

    @network_config.setter
    def network_config(self, value: CINetworkConfig):
        self._network_config = value

    @property
    def os_disk_path(self) -> pathlib.Path:
        return self._os_disk_path

    @property
    def ci_path(self) -> pathlib.Path:
        return self._ci_path

    @property
    def ci_img_path(self) -> pathlib.Path:
        return self._ci_img_path

    @property
    def vm_script_path(self) -> pathlib.Path:
        return self._vm_script_path

    @property
    def vm_script(self) -> VMScript:
        return self._vm_script

    @vm_script.setter
    def vm_script(self, value: VMScript):
        self._vm_script = value

    @property
    def ansible_inventory_path(self) -> pathlib.Path:
        return self._ansible_inventory_path

    @property
    def ansible_inventory(self) -> AnsibleInventory:
        return self._ansible_inventory

    @property
    def ansible_cfg_path(self) -> pathlib.Path:
        return self._ansible_cfg_path

    @property
    def ansible_playbook_path(self) -> pathlib.Path:
        return self._ansible_playbook_path

    @property
    def ansible_playbook(self) -> AnsiblePlaybook:
        return self._ansible_playbook

    def create(self):
        self.path.mkdir(parents=True, exist_ok=True)
        if not self.os_disk_path.exists():
            execute('qemu-img',
                    ['create', '-f', 'qcow2', '-b', self.backing_disk_path, '-F', 'qcow2', self.os_disk_path])
            console.log(f'Created OS disk at {self.os_disk_path} from backing store {self.backing_disk_path}')
            execute('qemu-img', ['resize', self.os_disk_path, self.os_disk_size])
            console.log(f'Resized OS disk at {self.os_disk_path} to {self.os_disk_size}')
        if not self.ci_img_path.exists():
            execute('dd', ['if=/dev/zero', f'of={self.ci_img_path}', 'bs=512', 'count=2880'])
            hdiutil_output = execute('hdiutil', ['attach', '-nomount', self.ci_img_path])
            kernel_device = hdiutil_output.stdout.strip()
            execute('diskutil', ['eraseVolume', 'MS-DOS', 'CIDATA', kernel_device])
            if self.metadata:
                meta_data_path = self.ci_path / 'meta-data'
                self.metadata.render_to(meta_data_path)
                shutil.copy(meta_data_path, '/Volumes/CIDATA/meta-data')
            if self.userdata:
                user_data_path = self.ci_path / 'user-data'
                self.userdata.render_to(user_data_path)
                shutil.copy(user_data_path, '/Volumes/CIDATA/user-data')
            if self.vendordata:
                vendor_data_path = self.ci_path / 'vendor-data'
                self.vendordata.render_to(vendor_data_path)
                shutil.copy(vendor_data_path, '/Volumes/CIDATA/vendor-data')
            if self.network_config:
                network_config_path = self.ci_path / 'network-config'
                self.network_config.render_to(network_config_path)
                shutil.copy(network_config_path, '/Volumes/CIDATA/network-config')
            execute('diskutil', ['eject', kernel_device])
            console.log(f'Created cloud-init disk image at {self.ci_img_path}')

        self._vm_script = VMScript(instance_id=self.instance_id,
                                   name=self.name,
                                   os_disk_path=self.os_disk_path,
                                   ci_img_path=self.ci_img_path)
        self._vm_script.vcpu = self.vcpu
        self._vm_script.ram = self.ram
        self._vm_script.mac = self.mac
        self.vm_script.render_to(self.vm_script_path)
        os.chmod(self.vm_script_path, mode=0o755)
        console.log(f'Created vm script at {self.vm_script_path}')
        console.log(f'[bold red]Start the instance using "sudo {self.vm_script_path}" now')

    def configure(self, actual_ip: str):
        self._ansible_inventory = AnsibleInventory(name=self.name, actual_ip=actual_ip)
        self.ansible_inventory.render_to(self.ansible_inventory_path)
        console.log(f'Created Ansible inventory at {self.ansible_inventory_path}')

        self._ansible_cfg = AnsibleCfg(inventory_path=self.ansible_inventory_path)
        self._ansible_cfg.render_to(self.ansible_cfg_path)

        self.ansible_playbook.render_to(self.ansible_playbook_path)
        console.log(f'Created Ansible playbook at {self.ansible_inventory_path}')

        resp = execute('ansible-playbook',
                       ['-i', self.ansible_inventory_path, self.ansible_playbook_path],
                       cwd=self.path)
        console.print(rich.panel.Panel.fit(resp.stdout,
                                           title='Ansible Output',
                                           subtitle=f'Instance {self.name} is configured.'))

    def remove(self):
        pass
