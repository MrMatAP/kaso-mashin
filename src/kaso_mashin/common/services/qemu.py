import subprocess

from kaso_mashin import KasoMashinException
from kaso_mashin.common import Service
from kaso_mashin.common.base_types import BinaryScale
from kaso_mashin.common.entities import InstanceEntity, NetworkKind, BootstrapKind


class QEMUService(Service):

    def __init__(self, runtime: "Runtime"):
        super().__init__(runtime)
        self._logger.info("Started QEMU service")

    def start_instance(self, instance: InstanceEntity) -> subprocess.Popen:
        args = [
            str(self._runtime.config.qemu_aarch64_path),
            "-name",
            instance.name,
            "-machine",
            "virt",
            "-cpu",
            "host",
            "-accel",
            "hvf",
            "-m",
            str(instance.ram.at_scale(BinaryScale.M).value),
            "-smp",
            str(instance.vcpu),
            "-object",
            "rng-random,id=rng0,filename=/dev/urandom",
            "-device",
            "virtio-rng-pci,rng=rng0",
            "-device",
            "virtio-gpu-pci",
            "-device",
            "nec-usb-xhci,id=usb-bus",
            "-device",
            "usb-kbd,bus=usb-bus.0",
            "-netdev",
            f"{instance.network.kind.value},"
            f"id=net0,"
            f"start-address={instance.network.dhcp_start},"
            f"end-address={instance.network.dhcp_end},"
            f"subnet-mask={instance.network.netmask}",
            "-device",
            f"virtio-net-device,netdev=net0,mac={instance.mac}",
            "-drive",
            f"if=virtio,file={instance.os_disk.path},format=qcow2,index=0,media=disk",
            "-vnc",
            "localhost:0,power-control=on",
        ]
        if instance.bootstrap.kind == BootstrapKind.IGNITION:
            args.extend(
                [
                    "-fw_cfg",
                    f"name=opt/org.flatcar-linux/config,file={instance.bootstrap_file}",
                    "-drive",
                    f"if=pflash,file={instance.uefi_code},format=raw,readonly=on",
                    "-drive",
                    f"if=pflash,file={instance.uefi_vars},format=raw",
                ]
            )
        if instance.bootstrap.kind == BootstrapKind.CLOUD_INIT:
            raise KasoMashinException(status=500, msg="Bootstrap init not supported")

        # args.extend(["-drive", f"file={instance.os_disk.path},media=disk,if=virtio,format=qcow2,cache=writethrough"])
        # args.extend(["-display", "cocoa", "-vnc", "to=0,power-control=on", "-device", "virtio-gpu-pci"])
        # args.extend(["-device", "VGA", "-display", "cocoa", "-vnc", "to=0,power-control=on"])
        # args.extend(["-display", "vnc=:0", "-vnc", "to=0,power-control=on"])

        return subprocess.Popen(args)
