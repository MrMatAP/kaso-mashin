import subprocess

from kaso_mashin import KasoMashinException
from kaso_mashin.common.ddd_scaffold import Service
from kaso_mashin.common.base_types import BinaryScale
from kaso_mashin.common.entities import InstanceEntity, NetworkKind, BootstrapKind


class QEMUService(Service):

    def __init__(self, runtime: 'Runtime'):
        self._runtime = runtime

    def start_instance(self, instance: InstanceEntity) -> subprocess.Popen:
        args = [
            self._runtime.config.qemu_binary_path,
            '-n', instance.name,
            '-machine', 'virt',
            '-cpu', 'host',
            '-accel', 'hvf',
            '-m', instance.ram.at_scale(BinaryScale.M).value,
            '-smp', instance.vcpu,
            '-object', 'rng-random,id=rng0,filename=/dev/urandom',
            '-device', 'virtio-rng-pci,rng=rng0',
            '-netdev', f'{instance.network.kind.value},'
                       f'id=net0,'
                       f'start-address={instance.network.dhcp_start},'
                       f'end-address={instance.network.dhcp_end},'
                       f'subnet_mask={instance.network.netmask}',
            '-device', f'virtio-net-device,'
                       f'netdev=net0,'
                       f'mac={instance.mac}',
            '-drive', f'if=none,id=blk,file={instance.os_disk.path}',
            '-device', 'virtio-blk-device,drive=blk'
        ]
        if instance.bootstrap.kind == BootstrapKind.IGNITION:
            args.extend([
                '-fw_cfg', f'name=opt/org.flatcar-linux/config,file={instance.bootstrap_file}',
                '-drive', f'if=pflash,file={instance.uefi_code},format=raw,readonly=on',
                '-drive', f'if=pflash,file={instance.uefi_vars},format=raw'
            ])
        if instance.bootstrap == BootstrapKind.CLOUD_INIT:
            raise KasoMashinException(status=500, msg='Bootstrap init not supported')

        return subprocess.Popen(args)
