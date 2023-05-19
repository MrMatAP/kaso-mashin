import os
import shutil
import argparse
from configparser import ConfigParser

from http.server import HTTPServer, BaseHTTPRequestHandler

from mrmat_playground import console
from mrmat_playground.abstract_resource_commands import AbstractResourceCommands
from mrmat_playground.executor import execute
from mrmat_playground.cloud_init import Metadata, UserData, VendorData, NetworkConfig

# TODO
test_pubkey = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD+Zo5EnA0fNi336bS8K0gpnmQ1csudD0bTZxkE4SzE7zGiD7Ybzb0vzkHVszYDC7H+2GEmeJAAn/t54kGPzCOsKomsqQXJ4h+MVLMmt9b01qBoObF02FFoPI1v/i9FWUGxr+WcyjvVzluGCSSSGMd/H6ri5o1Uo9ivy6PrbvxI1MARvVKBAhefjgJHNik1glZHMwVDCyMFNwSBlj8KV/pWoDT0cjVacTR0WoAcpxwfXHjx37FV15b/svelRsjPnzuW6UIk/gLqlvMIeIEubWriVi2DiRL4K3R2JMPHZ/VnEc/SVbilCjOZlsjCq/eqYd309ZeXAzytyGSaZrIWGQL9 imfeldma@bobeli.org'

class PhoneHomeServer(BaseHTTPRequestHandler):

    def do_POST(self):
        console.log(f'client_address: {self.client_address}')
        console.log(f'path: {self.path}')
        self.send_response(code=200, message='Well, hello there!')
        self.end_headers()

class InstanceCommands(AbstractResourceCommands):
    """
    Implementation of instance commands
    """

    @staticmethod
    def list(args: argparse.Namespace, config: ConfigParser) -> int:
        pass

    @staticmethod
    def get(args: argparse.Namespace, config: ConfigParser) -> int:
        pass

    @staticmethod
    def create(args: argparse.Namespace, config: ConfigParser) -> int:
        InstanceCommands._validate(config)

        instance_path = os.path.join(config['DEFAULT']['playground_path'], 'instances', args.name)
        disk_path = os.path.join(config['DEFAULT']['playground_path'], 'instances', args.name, 'cloud-init.img')
        backing_disk_path = os.path.join(config['DEFAULT']['playground_path'], 'images', 'jammy-arm64.qcow2')
        os_disk_path = os.path.join(config['DEFAULT']['playground_path'], 'instances', args.name, 'os.qcow2')
        bin_path = os.path.join(config['DEFAULT']['playground_path'], 'instances', args.name, 'vm.sh')
        inventory_path = os.path.join(config['DEFAULT']['playground_path'], 'instances', args.name, 'inventory.yml')
        playbook_path = os.path.join(config['DEFAULT']['playground_path'], 'ansible', 'test.yml')

        if not os.path.exists(backing_disk_path):
            console.log(f'Backing disk at {backing_disk_path} does not exist. Download the image first.')
            return 1
        if os.path.exists(instance_path):
            console.log(f'Instance at {instance_path} already exists. Remove the instance first.')
            return 1
        if os.path.exists(os_disk_path):
            console.log(f'Backing store at {os_disk_path} already exists. Remove the instance first.')
            return 1
        if os.path.exists(bin_path):
            console.log(f'Start script at {bin_path} already exists. Remove the instance first.')
            return 1
        if os.path.exists('/Volumes/CIDATA'):
            console.log('/Volumes/CIDATA is currently mounted. Unmount it first')
            return 1
        os.makedirs(instance_path)

        # Create a disk image
        execute('dd', ['if=/dev/zero', f'of={disk_path}', 'bs=512', 'count=2880'])
        hdiutil_output = execute('hdiutil', ['attach', '-nomount', disk_path])
        kernel_device = hdiutil_output.stdout.strip()
        execute('diskutil', ['eraseVolume', 'MS-DOS', 'CIDATA', kernel_device])
        with open('/Volumes/CIDATA/meta-data', mode='w', encoding='UTF-8') as m:
            m.write(Metadata(instance_id=args.name, hostname=args.name).render())
        with open('/Volumes/CIDATA/user-data', mode='w', encoding='UTF-8') as u:
            u.write(UserData(pubkey=test_pubkey).render())
        with open('/Volumes/CIDATA/vendor-data', mode='w', encoding='UTF-8') as v:
            v.write(VendorData().render())
        with open('/Volumes/CIDATA/network-config', mode='w', encoding='UTF-8') as n:
            n.write(NetworkConfig(mac='00:00:5e:00:52:02', ip='172.16.3.5/24', gw='172.16.3.1', ns='172.16.3.1').render())
        execute('diskutil', ['eject', kernel_device])
        console.log(f'Created cloud-init disk image at {disk_path}')

        # Create the OS disk
        execute('qemu-img', ['create', '-f', 'qcow2', '-b', backing_disk_path, '-F', 'qcow2', os_disk_path])
        console.log(f'Created OS disk at {os_disk_path} from backing store {backing_disk_path}')
        execute('qemu-img', ['resize', os_disk_path, args.os_disk_size])
        console.log(f'Resized OS disk at {os_disk_path} to {args.os_disk_size}')

        # Create the startscript
        with open(bin_path, mode='w', encoding='UTF-8') as b:
            b.write(f'''
#!/bin/bash
qemu-system-aarch64 \\
  -name {args.name} \\
  -machine virt \\
  -cpu host -accel hvf \\
  -smp 2 -m 4096 \\
  -bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd \\
  -chardev stdio,mux=on,id=char0 \\
  -mon chardev=char0,mode=readline \\
  -serial chardev:char0 \\
  -nographic \\
  -netdev vmnet-bridged,id=net.0,ifname=vlan1 \\
  -device virtio-net-pci,mac=00:00:5e:00:52:02,netdev=net.0 \\
  -device virtio-rng-pci \\
  -device nec-usb-xhci,id=usb-bus \\
  -device usb-kbd,bus=usb-bus.0 \\
  -drive if=virtio,file={os_disk_path},format=qcow2,cache=writethrough \\
  -drive if=virtio,file={disk_path},format=raw \\
  -smbios type=3,manufacturer=MrMat,version=0,serial={args.name},asset={args.name},sku={args.name}
            ''')
        os.chmod(bin_path, mode=0o755)
        console.log(f'Start the VM using "sudo {bin_path}')

        console.log('Waiting for the instance to phone home')
        httpd = HTTPServer(server_address=('172.16.3.10', 10300), RequestHandlerClass=PhoneHomeServer)
        httpd.timeout = 120
        httpd.handle_request()

        console.log(f'Instance {args.name} has phoned home')

        with open(inventory_path, mode='w', encoding='UTF-8') as i:
            i.write(f'''
all:
  vars:
    ansible_user: ansible
    ansible_become_user: root
    ansible_become: true
  hosts:
    {args.name}:
      ansible_host: 172.16.3.5
            ''')
        console.log(f'Created inventory at {inventory_path}')

        execute('ansible-playbook', ['-i', inventory_path, playbook_path])
        console.log('Instance postconfigured')
        return 0

    @staticmethod
    def modify(args: argparse.Namespace, config: ConfigParser) -> int:
        pass

    @staticmethod
    def remove(args: argparse.Namespace, config: ConfigParser) -> int:
        InstanceCommands._validate(config)
        instance_path = os.path.join(config['DEFAULT']['playground_path'], 'instances', f'{args.name}')
        if not os.path.exists(instance_path):
            console.log(f'Instance at {instance_path} does not exist')
            return 0
        shutil.rmtree(instance_path)
        console.log(f'Removed instance at {instance_path}')

    @staticmethod
    def _validate(config: ConfigParser):
        instances_path = os.path.join(config['DEFAULT']['playground_path'], 'instances')
        if not os.path.exists(instances_path):
            os.makedirs(instances_path)
            console.log(f'Created instances path at {instances_path}')
