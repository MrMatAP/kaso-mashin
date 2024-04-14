import argparse
import uuid
import ipaddress

import rich.table
import rich.box
import rich.columns

from kaso_mashin import console
from kaso_mashin.cli.commands import AbstractCommands
from kaso_mashin.common.entities import (
    NetworkListSchema, NetworkGetSchema, NetworkCreateSchema, NetworkModifySchema,
    NetworkKind
)


class NetworkCommands(AbstractCommands):
    """
    Implementation of the network command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        network_subparser = parser.add_subparsers()
        network_list_parser = network_subparser.add_parser(name='list', help='List networks')
        network_list_parser.set_defaults(cmd=self.list)
        network_get_parser = network_subparser.add_parser(name='get', help='Get a network')
        network_get_parser.add_argument('--uid',
                                        dest='uid',
                                        type=uuid.UUID,
                                        help='The network uid')
        network_get_parser.set_defaults(cmd=self.get)
        network_create_parser = network_subparser.add_parser(name='create', help='Create a network')
        network_create_parser.add_argument('-n', '--name',
                                           dest='name',
                                           type=str,
                                           required=True,
                                           help='The network name')
        network_create_parser.add_argument('-k', '--kind',
                                           dest='kind',
                                           type=NetworkKind,
                                           required=False,
                                           default=NetworkKind.VMNET_SHARED,
                                           help='The network kind')
        network_create_parser.add_argument('--cidr',
                                           dest='cidr',
                                           type=ipaddress.IPv4Network,
                                           required=True,
                                           help='The network CIDR')
        network_create_parser.add_argument('--gateway',
                                           dest='gateway',
                                           type=ipaddress.IPv4Address,
                                           required=True,
                                           help='The network gateway')
        network_create_parser.add_argument('--dhcp-start',
                                           dest='dhcp_start',
                                           type=ipaddress.IPv4Address,
                                           required=False,
                                           default=None,
                                           help='The DHCP start address')
        network_create_parser.add_argument('--dhcp-end',
                                           dest='dhcp_end',
                                           type=ipaddress.IPv4Address,
                                           required=False,
                                           default=None,
                                           help='The DHCP end address')
        network_create_parser.set_defaults(cmd=self.create)
        network_modify_parser = network_subparser.add_parser('modify', help='Modify a network')
        network_modify_parser.add_argument('--uid',
                                           dest='uid',
                                           type=uuid.UUID,
                                           required=True,
                                           help='The network uid')
        network_modify_parser.add_argument('-n', '--name',
                                           dest='name',
                                           type=str,
                                           required=False,
                                           default=None,
                                           help='The network name')
        network_modify_parser.add_argument('--cidr',
                                           dest='cidr',
                                           type=ipaddress.IPv4Network,
                                           required=False,
                                           default=None,
                                           help='The network CIDR')
        network_modify_parser.add_argument('--gateway',
                                           dest='gateway',
                                           type=ipaddress.IPv4Address,
                                           required=False,
                                           default=None,
                                           help='The network gateway')
        network_modify_parser.add_argument('--dhcp-start',
                                           dest='dhcp_start',
                                           type=ipaddress.IPv4Address,
                                           required=False,
                                           default=None,
                                           help='The DHCP start address')
        network_modify_parser.add_argument('--dhcp-end',
                                           dest='dhcp_end',
                                           type=ipaddress.IPv4Address,
                                           required=False,
                                           default=None,
                                           help='The DHCP end address')
        network_modify_parser.set_defaults(cmd=self.modify)
        network_remove_parser = network_subparser.add_parser('remove', help='Remove a network')
        network_remove_parser.add_argument('--uid',
                                           dest='uid',
                                           type=uuid.UUID,
                                           required=True,
                                           help='The network uid')
        network_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:
        del args
        resp = self.api_client(uri='/api/networks/', expected_status=[200])
        if not resp:
            return 1
        networks = [NetworkListSchema.model_validate(network) for network in resp.json()]
        table = NetworkListSchema.__rich_table()
        for network in networks:
            table.add_row(network.__rich_table_row())
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/networks/{args.uid}',
                               expected_status=[200],
                               fallback_msg=f'Network with id {args.uid} could not be found')
        if not resp:
            return 1
        network = NetworkGetSchema.model_validate_json(resp.content)
        console.print(network)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        schema = NetworkCreateSchema(name=args.name,
                                     kind=args.kind,
                                     cidr=args.cidr,
                                     gateway=args.gateway,
                                     dhcp_start=args.dhcp_start,
                                     dhcp_end=args.dhcp_end)
        resp = self.api_client(uri='/api/networks/',
                               method='POST',
                               schema=schema,
                               expected_status=[201],
                               fallback_msg='Failed to create network')
        if not resp:
            return 1
        network = NetworkGetSchema.model_validate_json(resp.content)
        console.print(network)
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = NetworkModifySchema(name=args.name,
                                     cidr=args.cidr,
                                     gateway=args.gateway,
                                     dhcp_start=args.dhcp_start,
                                     dhcp_end=args.dhcp_end)
        resp = self.api_client(uri=f'/api/networks/{args.uid}',
                               method='PUT',
                               schema=schema,
                               expected_status=[200],
                               fallback_msg='Failed to modify network')
        if not resp:
            return 1
        network = NetworkGetSchema.model_validate_json(resp.content)
        console.print(network)
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/networks/{args.uid}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove network')
        if not resp:
            return 1
        if resp.status_code == 204:
            console.print(f'Removed network with id {args.uid}')
        elif resp.status_code == 410:
            console.print(f'Network with id {args.uid} does not exist')
        return 0 if resp else 1
