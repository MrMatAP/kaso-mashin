from kaso_mashin import KasoMashinException
from kaso_mashin.model import InstanceModel, NetworkKind, BootstrapKind


class VMScriptModel:
    """
    Model for a VM script
    """

    def __init__(self, model: InstanceModel):
        self._model = model
        self._emulator = '/opt/homebrew/bin/qemu-system-aarch64'

    def render(self) -> str:
        base = [
                self._emulator,
                f'-machine {self.model.name}',
                '-machine virt',
                '-cpu host',
                '-accel hvf',
                f'-smp {self.model.vcpu}',
                f'-m {self.model.ram}',
                '-bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd',
                '-chardev stdio,mux=on,id=char0',
                '-mon chardev=char0,mode=readline',
                '-serial chardev:char0',
                '-nographic',
                '-device virtio-rng-pci',
                '-device nec-usb-xhci,id=usb-bus',
                '-device usb-kbd,bus=usb-bus.0',
                f'-drive if=virtio,file={self.model.os_disk_path},format=qcow2,cache=writethrough',
                f'-smbios type=3,manufacturer=MrMat,version=0,serial=instance_{self.model.instance_id},'
                f'asset={self.model.name},sku=MrMat']
        match self.model.network.kind:
            case NetworkKind.VMNET_HOST:
                base.append(f'-nic vmnet-host,'
                            f'start-address={self.model.network.dhcp4_start},'
                            f'end-address={self.model.network.dhcp4_end},'
                            f'subnet-mask={self.model.network.nm4},'
                            f'mac={self.model.mac}')
            case NetworkKind.VMNET_SHARED:
                base.append(f'-nic vmnet-shared,'
                            f'start-address={self.model.network.dhcp4_start},'
                            f'end-address={self.model.network.dhcp4_end},'
                            f'subnet-mask={self.model.network.nm4},'
                            f'mac={self.model.mac}')
            case NetworkKind.VMNET_BRIDGED:
                base.append(f'-nic vmnet-bridged,mac={self.model.mac},ifname=TODO')
            case _:
                raise KasoMashinException(status=400,
                                          msg=f'There is no network kind {self.model.network.kind}')
        match self.model.bootstrapper:
            case BootstrapKind.NONE.value:
                pass
            case BootstrapKind.CI.value:
                raise KasoMashinException(status=400,
                                          msg=f'Bootstrapper {self.model.bootstrapper} is not yet implemented')
            case BootstrapKind.CI_DISK.value:
                base.append(f'-drive if=virtio,file={self.model.ci_disk_path},format=raw')
            case BootstrapKind.IGNITION.value:
                raise KasoMashinException(status=400,
                                          msg=f'Bootstrapper {self.model.bootstrapper} is not yet implemented')
            case _:
                raise KasoMashinException(status=400,
                                          msg=f'There is no bootstrapper {self.model.bootstrapper}')
        script = ' \\\n  '.join(base)
        return f'#!/bin/bash\n# This script can be used to manually start the instance it is located in\n\n{script}'

    @property
    def model(self) -> InstanceModel:
        return self._model
