import argparse
import configparser

import rich.table

from mrmat_playground import console
from mrmat_playground.model import Cloud


class CloudCommands:
    """
    Commands involving the cloud
    """

    @staticmethod
    def get(args: argparse.Namespace, config: configparser.ConfigParser) -> int:    # pylint: disable=unused-argument
        cloud = Cloud(path=args.path)
        cloud.load()
        table = rich.table.Table(title=f'Cloud Playground: {cloud.name}')
        table.add_column('Key')
        table.add_column('Value')
        table.add_row('Name:', cloud.name)
        table.add_row('Path:', str(cloud.path))
        table.add_row('Admin Password:', cloud.admin_password)
        table.add_row('Public Key Path:', str(cloud.public_key_path))
        table.add_row('Host Interface:', cloud.host_if)
        table.add_row('Host IPv4 Address:', cloud.host_ip4)
        table.add_row('Host IPv4 Netmask:', cloud.host_nm4)
        table.add_row('Host IPv4 Gateway:', cloud.host_gw4)
        table.add_row('Host IPv4 Nameserver:', cloud.host_ns4)
        table.add_row('Phone Home Port:', str(cloud.ph_port))
        console.print(table)
        return 0

    @staticmethod
    def create(args: argparse.Namespace, config: configparser.ConfigParser) -> int:  # pylint: disable=unused-argument
        cloud = Cloud(path=args.path)
        cloud.name = args.name
        cloud.public_key_path = args.public_key_path
        cloud.admin_password = args.admin_password
        cloud.host_if = args.host_if
        cloud.host_ip4 = args.host_ip4
        cloud.host_nm4 = args.host_nm4
        cloud.host_gw4 = args.host_gw4
        cloud.host_ns4 = args.host_ns4
        cloud.ph_port = args.ph_port
        return cloud.create()
