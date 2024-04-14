import argparse
import uuid
import ipaddress

from kaso_mashin import console
from kaso_mashin.cli.commands import BaseCommands
from kaso_mashin.common.config import Config
from kaso_mashin.common.entities import (
    NetworkListSchema, NetworkGetSchema, NetworkCreateSchema, NetworkModifySchema,
    NetworkKind
)


class NetworkCommands(BaseCommands[NetworkListSchema, NetworkGetSchema]):
    """
    Implementation of the network command group
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self._prefix = '/api/networks'
        self._list_schema_type = NetworkListSchema
        self._get_schema_type = NetworkGetSchema

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

    def create(self, args: argparse.Namespace) -> int:
        schema = NetworkCreateSchema(name=args.name,
                                     kind=args.kind,
                                     cidr=args.cidr,
                                     gateway=args.gateway,
                                     dhcp_start=args.dhcp_start,
                                     dhcp_end=args.dhcp_end)
        resp = self._api_client(uri='/api/networks/',
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
        resp = self._api_client(uri=f'/api/networks/{args.uid}',
                                method='PUT',
                                schema=schema,
                                expected_status=[200],
                                fallback_msg='Failed to modify network')
        if not resp:
            return 1
        network = NetworkGetSchema.model_validate_json(resp.content)
        console.print(network)
        return 0
