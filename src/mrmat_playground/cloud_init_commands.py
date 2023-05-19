import os
import argparse
from configparser import ConfigParser

from mrmat_playground import console
from mrmat_playground.abstract_resource_commands import AbstractResourceCommands
from mrmat_playground.executor import execute


class CloudInitCommands(AbstractResourceCommands):
    """
    Implementation of cloud-init commands
    """

    @staticmethod
    def list(args: argparse.Namespace, config: ConfigParser) -> int:
        pass

    @staticmethod
    def get(args: argparse.Namespace, config: ConfigParser) -> int:
        pass

    @staticmethod
    def create(args: argparse.Namespace, config: ConfigParser) -> int:
        CloudInitCommands._validate(config)
        disk_path = os.path.join(config['DEFAULT']['playground_path'], 'disks', f'{args.name}.img')
        if os.path.exists(disk_path):
            console.log(f'Cloud-init disk image at {disk_path} already exists')
            return 1
        if os.path.exists('/Volumes/CIDATA'):
            console.log('/Volumes/CIDATA is currently mounted. Unmount it first')
            return 1
        execute('dd', ['if=/dev/zero', f'of={disk_path}', 'bs=512', 'count=2880'])
        hdiutil_output = execute('hdiutil', ['attach', '-nomount', disk_path])
        kernel_device = hdiutil_output.stdout.strip()
        execute('diskutil', ['eraseVolume', 'MS-DOS', 'CIDATA', kernel_device])
        # TODO: Create the disk content
        execute('diskutil', ['eject', kernel_device])
        console.log(f'Created cloud-init disk image at {disk_path}')
        return 0

    @staticmethod
    def modify(args: argparse.Namespace, config: ConfigParser) -> int:
        pass

    @staticmethod
    def remove(args: argparse.Namespace, config: ConfigParser) -> int:
        CloudInitCommands._validate(config)
        disk_path = os.path.join(config['DEFAULT']['playground_path'], 'disks', f'{args.name}.img')
        if not os.path.exists(disk_path):
            console.log(f'Cloud-init disk image at {disk_path} does not exist')
            return 0
        os.unlink(disk_path)
        console.log(f'Removed cloud-init disk image at {disk_path}')
        return 0

    @staticmethod
    def _validate(config: ConfigParser):
        playground_disks_path = os.path.join(config['DEFAULT']['playground_path'], 'disks')
        if not os.path.exists(playground_disks_path):
            os.makedirs(playground_disks_path)
            console.log(f'Created cloud-init disks path at {playground_disks_path}')
