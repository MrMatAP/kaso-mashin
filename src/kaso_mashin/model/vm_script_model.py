import pathlib
from kaso_mashin.model import Renderable, InstanceModel


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
        return f'''
#!/bin/bash
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
  -netdev vmnet-bridged,id=net.0,ifname=vlan1 \\
  -device virtio-net-pci,mac={self.instance.mac},netdev=net.0 \\
  -device virtio-rng-pci \\
  -device nec-usb-xhci,id=usb-bus \\
  -device usb-kbd,bus=usb-bus.0 \\
  -drive if=virtio,file={self.instance.os_disk_path},format=qcow2,cache=writethrough \\
  -drive if=virtio,file=TODO,format=raw \\
  -smbios type=3,manufacturer=MrMat,version=0,serial=instance_{self.instance.instance_id},asset={self.instance.name},sku=MrMat
                    '''
