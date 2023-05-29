import pathlib
from .renderable import Renderable


class VMScript(Renderable):
    """
    Renders a VM script
    """

    def __init__(self, instance_id: str, name: str, os_disk_path: pathlib.Path, ci_img_path: pathlib.Path):
        self._instance_id = instance_id
        self._name = name
        self._os_disk_path = os_disk_path
        self._ci_img_path = ci_img_path
        self._vcpu = 2
        self._ram = 2048
        self._mac = None

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def name(self) -> str:
        return self._name

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
        self._mac = value

    @property
    def os_disk_path(self) -> pathlib.Path:
        return self._os_disk_path

    @property
    def ci_img_path(self) -> pathlib.Path:
        return self._ci_img_path

    def render(self) -> str:
        return f'''
#!/bin/bash
qemu-system-aarch64 \\
  -name {self.name} \\
  -machine virt \\
  -cpu host -accel hvf \\
  -smp {self.vcpu} -m {self.ram} \\
  -bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd \\
  -chardev stdio,mux=on,id=char0 \\
  -mon chardev=char0,mode=readline \\
  -serial chardev:char0 \\
  -nographic \\
  -netdev vmnet-bridged,id=net.0,ifname=vlan1 \\
  -device virtio-net-pci,mac={self.mac},netdev=net.0 \\
  -device virtio-rng-pci \\
  -device nec-usb-xhci,id=usb-bus \\
  -device usb-kbd,bus=usb-bus.0 \\
  -drive if=virtio,file={self.os_disk_path},format=qcow2,cache=writethrough \\
  -drive if=virtio,file={self.ci_img_path},format=raw \\
  -smbios type=3,manufacturer=MrMat,version=0,serial={self.instance_id},asset={self.name},sku=MrMat
                    '''
