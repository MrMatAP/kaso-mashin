import pathlib

from kaso_mashin import KasoMashinException
from kaso_mashin.model import Renderable, InstanceModel, NetworkKind


class VMScriptModel(Renderable):
    """
    Renders a VM script
    """

    def __init__(self, instance: InstanceModel, path: pathlib.Path):
        self._instance = instance
        self.render_to(path)

    @property
    def instance(self) -> InstanceModel:
        return self._instance

    def render(self) -> str:
        base = f'''#!/bin/bash
qemu-system-aarch64 \\
  -name {self.instance.name} \\
  -machine virt \\
  -cpu host -accel hvf \\
  -smp {self.instance.vcpu} -m {self.instance.ram} \\
  -bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd \\
  -chardev stdio,mux=on,id=char0 \\
  -mon chardev=char0,mode=readline \\
  -serial chardev:char0 \\
  -nographic \\
  -device virtio-rng-pci \\
  -device nec-usb-xhci,id=usb-bus \\
  -device usb-kbd,bus=usb-bus.0 \\
  -drive if=virtio,file={self.instance.os_disk_path},format=qcow2,cache=writethrough \\
  -smbios type=3,manufacturer=MrMat,version=0,serial=instance_{self.instance.instance_id},asset={self.instance.name},sku=MrMat \\
'''
        match self.instance.network.kind:
            case NetworkKind.VMNET_HOST:
                base += f'  -nic vmnet-host,' \
                        f'start-address={self.instance.network.dhcp_start},' \
                        f'end-address={self.instance.network.dhcp_end},' \
                        f'subnet-mask={self.instance.network.nm4},' \
                        f'mac={self.instance.mac} \\\n'
            case NetworkKind.VMNET_SHARED:
                base += f'  -nic vmnet-bridged,mac={self.instance.mac} \n\\'
            case _:
                raise KasoMashinException(status=400,
                                          msg=f'There is no network kind {self.instance.network.kind}')
        match self.instance.bootstrapper:
            case 'none':
                pass
            case 'ci':
                raise KasoMashinException(status=500,
                                          msg=f'Bootstrapper {self.instance.bootstrapper} is not yet implemented')
            case 'ci-static':
                base += f'  -drive if=virtio,file={self.instance.ci_disk_path},format=raw'
            case _:
                raise KasoMashinException(status=400,
                                          msg=f'There is no bootstrapper {self.instance.bootstrapper}')
        return base
