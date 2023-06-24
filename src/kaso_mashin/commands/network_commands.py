import argparse

import rich.tree
import rich.table
import rich.columns

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import NetworkKind, NetworkModel


class NetworkCommands(AbstractCommands):
    """
    Implementation of the network command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        network_subparser = parser.add_subparsers()
        network_list_parser = network_subparser.add_parser(name='list', help='List networks')
        network_list_parser.set_defaults(cmd=self.list)
        network_get_parser = network_subparser.add_parser(name='get', help='Get a network')
        network_get_parser.add_argument('--id',
                                        dest='id',
                                        type=int,
                                        required=True,
                                        help='The network id')
        network_get_parser.set_defaults(cmd=self.get)
        network_create_parser = network_subparser.add_parser(name='create', help='Create a network')
        network_create_parser.add_argument('-n', '--name',
                                           dest='name',
                                           type=str,
                                           required=True,
                                           help='The network name')
        network_create_parser.add_argument('-k', '--kind',
                                           dest='kind',
                                           type=str,
                                           required=False,
                                           choices=[k.value for k in list(NetworkKind)],
                                           help='The network kind')
        network_create_parser.add_argument('--host-ip4',
                                           dest='host_ip4',
                                           type=str,
                                           required=True,
                                           help='The IPv4 address of the host')
        network_create_parser.add_argument('--host-phone-home-port',
                                           dest='host_phone_home_port',
                                           type=int,
                                           required=False,
                                           default=self.config.default_phone_home_port,
                                           help='The port on which the host listens for VMs to phone home')
        network_create_parser.add_argument('--nm4',
                                           dest='nm4',
                                           type=str,
                                           required=True,
                                           help='The IPv4 netmask')
        network_create_parser.add_argument('--gw4',
                                           dest='gw4',
                                           type=str,
                                           required=True,
                                           help='The IPv4 gateway address')
        network_create_parser.add_argument('--ns4',
                                           dest='ns4',
                                           type=str,
                                           required=True,
                                           help='The IPv4 address of the DNS nameserver')
        network_create_parser.add_argument('--dhcp-start',
                                           dest='dhcp_start',
                                           type=str,
                                           required=False,
                                           help='Optional DHCP start address for vmnet-host networks')
        network_create_parser.add_argument('--dhcp-end',
                                           dest='dhcp_end',
                                           type=str,
                                           required=False,
                                           help='Optional DHCP end address for vmnet-host networks')
        network_create_parser.set_defaults(cmd=self.create)
        network_modify_parser = network_subparser.add_parser('modify', help='Modify a network')
        network_modify_parser.add_argument('--id',
                                           dest='id',
                                           type=int,
                                           required=True,
                                           help='The network id')
        network_modify_parser.add_argument('-n', '--name',
                                           dest='name',
                                           type=str,
                                           required=False,
                                           help='The network name')
        network_modify_parser.add_argument('-k', '--kind',
                                           dest='kind',
                                           type=NetworkKind,
                                           required=False,
                                           choices=[k.value for k in list(NetworkKind)],
                                           help='The network kind')
        network_modify_parser.add_argument('--host-ip4',
                                           dest='host_ip4',
                                           type=str,
                                           required=False,
                                           help='The IPv4 address of the host')
        network_modify_parser.add_argument('--nm4',
                                           dest='nm4',
                                           type=str,
                                           required=False,
                                           help='The IPv4 netmask')
        network_modify_parser.add_argument('--gw4',
                                           dest='gw4',
                                           type=str,
                                           required=False,
                                           help='The IPv4 gateway address')
        network_modify_parser.add_argument('--ns4',
                                           dest='ns4',
                                           type=str,
                                           required=False,
                                           help='The IPv4 address of the DNS nameserver')
        network_modify_parser.set_defaults(cmd=self.modify)
        network_remove_parser = network_subparser.add_parser('remove', help='Remove a network')
        network_remove_parser.add_argument('--id',
                                           dest='id',
                                           type=int,
                                           required=True,
                                           help='The network id')
        network_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:        # pylint: disable=unused-argument
        networks = self.network_controller.list()
        tree = rich.tree.Tree(label='Networks')
        for network in networks:
            ntree = tree.add(label=f'{network.network_id}: {network.name}')
            ntree.add(rich.columns.Columns(['Id:', str(network.network_id)]))
            ntree.add(rich.columns.Columns(['Name:', network.name]))
            ntree.add(rich.columns.Columns(['Kind:', network.kind.value]))
            ntree.add(rich.columns.Columns(['Host IP4:', network.host_ip4]))
            ntree.add(rich.columns.Columns(['Netmask4:', network.nm4]))
            ntree.add(rich.columns.Columns(['Gateway4:', network.gw4]))
            ntree.add(rich.columns.Columns(['Nameserver4:', network.ns4]))
            ntree.add(rich.columns.Columns(['Phone home port:', str(network.host_phone_home_port)]))
        console.print(tree)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        network = self.network_controller.get(args.id)
        if not network:
            console.print(f'ERROR: Network with id {args.id} not found')
            return 1
        console.print(f'- Id:          {network.network_id}')
        console.print(f'  Name:        {network.name}')
        console.print(f'  Kind:        {network.kind.value}')
        console.print(f'  Host IP4:    {network.host_ip4}')
        console.print(f'  Netmask4:    {network.nm4}')
        console.print(f'  Gateway4:    {network.gw4}')
        console.print(f'  Nameserver4: {network.ns4}')
        console.print(f'  Phone home port: {network.host_phone_home_port}')
        return 0

    def create(self, args: argparse.Namespace) -> int:
        model = NetworkModel(name=args.name,
                             kind=NetworkKind(args.kind),
                             host_ip4=args.host_ip4,
                             nm4=args.nm4,
                             gw4=args.gw4,
                             ns4=args.ns4,
                             host_phone_home_port=args.host_phone_home_port,
                             dhcp_start=args.dhcp_start,
                             dhcp_end=args.dhcp_end)
        self.network_controller.create(model)
        console.print(f'Created network {model.network_id}: {args.name}')
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        update = self.network_controller.get(args.id)
        if not update:
            console.print(f'Network id {args.id} not found')
            return 1
        update.kind = args.kind
        update.host_ip4 = args.host_ip4
        update.nm4 = args.nm4
        update.gw4 = args.gw4
        update.ns4 = args.ns4
        update.host_phone_home_port = args.host_phone_home_port
        self.network_controller.modify(args.id, update)
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        self.network_controller.remove(args.id)
        return 0
