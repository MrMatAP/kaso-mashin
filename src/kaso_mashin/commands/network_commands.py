import argparse

import rich.table
import rich.box
import rich.columns

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import NetworkKind, NetworkSchema, NetworkCreateSchema, NetworkModifySchema


class NetworkCommands(AbstractCommands):
    """
    Implementation of the network command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        network_subparser = parser.add_subparsers()
        network_list_parser = network_subparser.add_parser(name='list', help='List networks')
        network_list_parser.set_defaults(cmd=self.list)
        network_get_parser = network_subparser.add_parser(name='get', help='Get a network')
        network_get_id_or_name = network_get_parser.add_mutually_exclusive_group(required=True)
        network_get_id_or_name.add_argument('--id',
                                            dest='network_id',
                                            type=int,
                                            help='The network id')
        network_get_id_or_name.add_argument('--name',
                                            dest='name',
                                            type=str,
                                            help='The network name')
        network_get_id_or_name.set_defaults(cmd=self.get)
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
                                           choices=[k.value for k in NetworkKind],
                                           help='The network kind')
        network_create_parser.add_argument('--host-phone-home-port',
                                           dest='host_phone_home_port',
                                           type=int,
                                           required=False,
                                           default=self.config.default_phone_home_port,
                                           help='The port on which the host listens for VMs to phone home')
        network_create_parser.add_argument('--ns4',
                                           dest='ns4',
                                           type=str,
                                           required=True,
                                           help='The IPv4 address of the DNS nameserver')
        network_create_parser.add_argument('--dhcp-start',
                                           dest='dhcp4_start',
                                           type=str,
                                           required=False,
                                           help='Optional DHCP start address for host and shared networks')
        network_create_parser.add_argument('--dhcp-end',
                                           dest='dhcp4_end',
                                           type=str,
                                           required=False,
                                           help='Optional DHCP end address for host and shared networks')
        network_create_parser.set_defaults(cmd=self.create)
        network_modify_parser = network_subparser.add_parser('modify', help='Modify a network')
        network_modify_parser.add_argument('--id',
                                           dest='network_id',
                                           type=int,
                                           required=True,
                                           help='The network id')
        network_modify_parser.add_argument('--host-phone-home-port',
                                           dest='host_phone_home_port',
                                           type=int,
                                           required=False,
                                           help='The port on which the host listens for VMs to phone home')
        network_modify_parser.add_argument('--ns4',
                                           dest='ns4',
                                           type=str,
                                           required=False,
                                           help='The IPv4 address of the DNS nameserver')
        network_modify_parser.add_argument('--dhcp-start',
                                           dest='dhcp4_start',
                                           type=str,
                                           required=False,
                                           help='Optional DHCP start address for host and shared networks')
        network_modify_parser.add_argument('--dhcp-end',
                                           dest='dhcp4_end',
                                           type=str,
                                           required=False,
                                           help='Optional DHCP end address for host and shared networks')
        network_modify_parser.set_defaults(cmd=self.modify)
        network_remove_parser = network_subparser.add_parser('remove', help='Remove a network')
        network_remove_parser.add_argument('--id',
                                           dest='network_id',
                                           type=int,
                                           required=True,
                                           help='The network id')
        network_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
        resp = self.api_client(uri='/api/networks/', expected_status=[200])
        if not resp:
            return 1
        networks = [NetworkSchema.model_validate(network) for network in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]ID')
        table.add_column('[blue]Kind')
        table.add_column('[blue]Name')
        for network in networks:
            table.add_row(str(network.network_id), network.name, str(network.kind.value))
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/networks/{args.network_id}',
                               expected_status=[200],
                               fallback_msg=f'Network with id {args.network_id} could not be found')
        if not resp:
            return 1
        network = NetworkSchema.model_validate_json(resp.content)
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]Id', str(network.network_id))
        table.add_row('[blue]Name', network.name)
        table.add_row('[blue]Kind', str(network.kind.value))
        table.add_row('[blue]Host interface', network.host_if)
        table.add_row('[blue]Host IPv4', str(network.host_ip4))
        table.add_row('[blue]Gateway4', str(network.gw4))
        table.add_row('[blue]Nameserver4', str(network.gw4))
        table.add_row('[blue]DHCPv4 Start', str(network.dhcp4_start))
        table.add_row('[blue]DHCPv4 End', str(network.dhcp4_end))
        table.add_row('[blue]Phone home port', str(network.host_phone_home_port))
        console.print(table)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        schema = NetworkCreateSchema(name=args.name,
                                     kind=args.kind,
                                     ns4=args.ns4,
                                     dhcp4_start=args.dhcp4_start,
                                     dhcp4_end=args.dhcp4_end,
                                     host_phone_home_port=args.host_phone_home_port)
        resp = self.api_client(uri='/api/networks',
                               method='POST',
                               body=schema.model_dump(),
                               expected_status=[201],
                               fallback_msg='Failed to create network')
        if not resp:
            return 1
        network = NetworkSchema.model_validate_json(resp.content)
        console.print(f'Created network with id {network.network_id}')
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = NetworkModifySchema(ns4=args.ns4,
                                     dhcp4_start=args.dhcp4_start,
                                     dhcp4_end=args.dhcp4_end,
                                     host_phone_home_port=args.host_phone_home_port)
        resp = self.api_client(uri=f'/api/networks/{args.network_id}',
                               method='PUT',
                               body=schema.model_dump(),
                               expected_status=[200],
                               fallback_msg='Failed to modify network')
        return 0 if resp else 1

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/networks/{args.network_id}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove network')
        return 0 if resp else 1
