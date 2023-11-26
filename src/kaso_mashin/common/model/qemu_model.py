import logging
import time
import typing
import subprocess
import shlex
import netifaces
from http.server import HTTPServer, BaseHTTPRequestHandler

from kaso_mashin import KasoMashinException
from .instance_model import DisplayKind, InstanceModel
from .network_model import NetworkKind
from .bootstrap_model import BootstrapKind


class PhoneHomeServer(HTTPServer):
    """
    A small server waiting for an instance to call home. We override this to pass it a function to be called
    with the actual IP address the instance has. We can't do this in the handler because it is statically
    referred to by the PhoneHomeServer
    """

    def __init__(self,
                 server_address: tuple[str, int],
                 RequestHandlerClass: typing.Callable,
                 callback: typing.Callable,
                 bind_and_activate: bool = ...) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self._callback = callback
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')

    @property
    def callback(self):
        return self._callback

    @property
    def logger(self):
        return self._logger


class PhoneHomeHandler(BaseHTTPRequestHandler):
    """
    A handler for instances calling their mum
    """

    # It is actually required to be called do_POST, despite pylint complaining about it
    def do_POST(self):              # pylint: disable=invalid-name
        self.log_request()
        self.server.logger.info(f'Instance phone home with {self.client_address[0]}')
        self.server.logger.info(f'Request line: {self.requestline}')
        self.server.callback(self.client_address[0])
        self.send_response(code=200, message='Well, hello there!')
        self.end_headers()


class QEmuModel:
    """
    Model for a VM running in QEmu
    """

    def __init__(self, model: InstanceModel):
        self._model = model
        self._emulator = '/opt/homebrew/bin/qemu-system-aarch64'
        self._cmd = self._generate_cmd()
        self._process: subprocess.Popen | None = None
        self._logger = logging.getLogger(f'{self.__class__.__module__}.{self.__class__.__name__}')
        self._logger.info('Initialised for %s', model.name)

    def _generate_cmd(self) -> str:
        cmd = (f'{self.emulator} -name {self.model.name} -machine virt -cpu host -accel hvf '
               f'-smp {self.model.vcpu} -m {self.model.ram} '
               f'-bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd '
               '-device virtio-rng-pci -device nec-usb-xhci,id=usb-bus -device usb-kbd,bus=usb-bus.0 '
               f'-drive if=virtio,file={self.model.os_disk_path},format=qcow2,cache=writethrough '
               f'-smbios type=3,manufacturer=MrMat,version=0,serial=instance_{self.model.instance_id},'
               f'asset={self.model.name},sku=MrMat '
               f'-chardev socket,id=char0,server=on,wait=off,path={self.model.console_path} '
               f'-qmp unix:{self.model.qmp_path},server=on,wait=off ')
        match self.model.display:
            case DisplayKind.VNC:
                cmd += ('-device usb-tablet '
                        f'-vnc unix:{self.model.vnc_path},password=off,power-control=on '
                        '-display none ')
            case DisplayKind.COCOA:
                cmd += '-device usb-tablet -display cocoa '
            case DisplayKind.HEADLESS:
                cmd += '-display none '
            case _:
                raise KasoMashinException(status=400, msg=f'There is no display kind {self.model.display.kind}')
        match self.model.network.kind:
            case NetworkKind.VMNET_HOST:
                cmd += (f'-nic vmnet-host,'
                        f'start-address={self.model.network.dhcp4_start},'
                        f'end-address={self.model.network.dhcp4_end},'
                        f'subnet-mask={self.model.network.nm4},'
                        f'mac={self.model.mac} ')
            case NetworkKind.VMNET_SHARED:
                cmd += (f'-nic vmnet-shared,'
                        f'start-address={self.model.network.dhcp4_start},'
                        f'end-address={self.model.network.dhcp4_end},'
                        f'subnet-mask={self.model.network.nm4},'
                        f'mac={self.model.mac} ')
            case NetworkKind.VMNET_BRIDGED:
                cmd += f'-nic vmnet-bridged,mac={self.model.mac},ifname=TODO '
            case _:
                raise KasoMashinException(status=400, msg=f'There is no network kind {self.model.network.kind}')
        match self.model.bootstrapper:
            case BootstrapKind.NONE.value:
                pass
            case BootstrapKind.CI.value:
                raise KasoMashinException(status=400,
                                          msg=f'Bootstrapper {self.model.bootstrapper} is not yet implemented')
            case BootstrapKind.CI_DISK.value:
                cmd += f'-drive if=virtio,file={self.model.ci_disk_path},format=raw '
            case BootstrapKind.IGNITION.value:
                raise KasoMashinException(status=400,
                                          msg=f'Bootstrapper {self.model.bootstrapper} is not yet implemented')
            case _:
                raise KasoMashinException(status=400,
                                          msg=f'There is no bootstrapper {self.model.bootstrapper}')
        return cmd

    def generate_script(self):
        with open(self.model.vm_script_path, mode='w', encoding='UTF-8') as v:
            v.write(f'#!/bin/bash\n# '
                    f'This script can be used to manually start the instance it is located in'
                    f'\n\n{self._generate_cmd()}')
        self.model.vm_script_path.chmod(0o755)

    def _wait_for_bridge(self) -> bool | None:
        # if2addr = {}
        # addr2if = {}
        # for iface in netifaces.interfaces():
        #     for ip in netifaces.ifaddresses(iface).get(netifaces.AF_INET, []):
        #         if2addr[iface] = [ip.get('addr')]
        #         addr2if[ip.get('addr')] = iface
        addr2if = {}
        for br in list(filter(lambda e: e.startswith('bridge'), netifaces.interfaces())):
            for ip in netifaces.ifaddresses(br).get(netifaces.AF_INET, []):
                addr2if[ip.get('addr')] = br
        return self.model.network.host_ip4 in addr2if

    def start(self):
        # pylint: disable=consider-using-with
        self.process = subprocess.Popen(args=shlex.split(self._generate_cmd()), encoding='UTF-8')
        self._logger.info('Started QEmu process')
        # TODO: Cloud-init will only ever phone home once per instance, unless we make it a runcmd
        # Wait for the bridge to come up
        attempt = 0
        while attempt < 15 and not self._wait_for_bridge():
            self._logger.info('Waiting for bridge to come up (%s/15)', attempt)
            attempt += 1
            time.sleep(1)
        if attempt == 9:
            raise KasoMashinException(status=500, msg='Bridge never came up')
        self._logger.info('Bridge has come up')

        def _instance_phoned_home(actual_ip: str):
            self._logger.info('Instance has phoned home. Actual IP: %s', actual_ip)

        self._logger.info('Starting phone home server on host %s', self.model.network.host_ip4)
        httpd = PhoneHomeServer(server_address=(str(self.model.network.host_ip4),
                                                self.model.network.host_phone_home_port),
                                callback=_instance_phoned_home,
                                RequestHandlerClass=PhoneHomeHandler)
        httpd.timeout = 60
        httpd.handle_request()
        self._logger.info('Instance has started')

    def stop(self):
        if self.process:
            self._logger.info('Stopping instance')
            self.process.terminate()

    @property
    def model(self):
        return self._model

    @property
    def emulator(self):
        return self._emulator

    @property
    def process(self):
        return self._process

    @process.setter
    def process(self, value):
        self._process = value
