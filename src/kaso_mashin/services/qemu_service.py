import subprocess

import kaso_mashin
import kaso_mashin.base
from kaso_mashin.domain.instance import Instance
from kaso_mashin.domain.bootstrap import BootstrapKind


class QEMUService:

    def start_instance(self, instance: Instance) -> subprocess.Popen:
        try:
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
                str(instance.ram.at_scale(kaso_mashin.base.BinaryScale.M).value),
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
            ]
            # Add options for forwarding the serial console and mon
            # TODO: We're doing telnet for now until we can hookup the frontends to this
            # TODO: This actually works with telnet when you expose it via
            #       sudo socat UNIX:/path/to/console.sock TCP-LISTEN:5701
            args.extend([
                "-nographic",
                "-chardev",
                f"socket,id=char0,server=on,wait=off,telnet=on,path={instance.path.joinpath('console.sock')}",
                "-serial",
                "chardev:char0"
                "-chardev",
                f"socket,id=char1,server=on,wait=off,telnet=on,path={instance.path.joinpath('qmp.sock')}",
                "-mon",
                "chardev=char1,mode=readline",
            ])
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
                raise kaso_mashin.base.KasoMashinException(status=500, msg="Bootstrap init not supported")

            return subprocess.Popen(args)
        except Exception as e:
            raise kaso_mashin.base.KasoMashinException(status=500, msg=str(e))
