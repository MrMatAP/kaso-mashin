import subprocess
import shlex
import qemu.qmp

from kaso_mashin.model import InstanceModel


class InstanceProcess:
    """
    An instance
    """

    def __init__(self, model: InstanceModel):
        self._model = model

    async def start(self):
        try:
            vm = subprocess.Popen(shlex.split('/opt/homebrew/bin/qemu-system-aarch64',
                                              '-name host -machine virt -cpu host -accel hvf -smp 2 -m 2048 '
                                              '-bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd '
                                              '-nographic '
                                              '-device virtio-rng-pci '
                                              '-device nec-usb-xhci,id=usb-bus '
                                              '-device usb-kbd,bus=usb-bus.0 '
                                              '-drive if=virtio,file=/Users/imfeldma/var/kaso/instances/host/os.qcow2,format=qcow2,cache=writethrough '
                                              '-smbios type=3,manufacturer=MrMat,version=0,serial=instance_1,asset=host,sku=MrMat '
                                              '-nic vmnet-shared,start-address=172.16.4.100,end-address=172.16.4.254,subnet-mask=255.255.255.0,mac=00:50:56:00:00:01 '
                                              '-drive if=virtio,file=/Users/imfeldma/var/kaso/instances/host/ci.img,format=raw '
                                              '-qmp unix:/Users/imfeldma/var/kaso/instances/host/host.sock,server=on,wait=off'),
                                  stdin=None,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  encoding='UTF-8')
            qmp = qemu.qmp.QMPClient('host')
            await qmp.connect('/Users/imfeldma/var/kaso/instances/host/host.sock')
            res = await qmp.execute('query-status')
            print(f'VM status: {res["status"]}')
            await qmp.disconnect
            vm.terminate()
        except Exception as e:
            print(e)

    def stop(self):
        pass

    @property
    def model(self):
        return self._model
