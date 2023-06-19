import argparse
import pathlib

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import IdentityModel


class IdentityCommands(AbstractCommands):
    """
    Implementation of the identity command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        identity_subparser = parser.add_subparsers()
        identity_list_parser = identity_subparser.add_parser(name='list', help='List identities')
        identity_list_parser.set_defaults(cmd=self.list)
        identity_get_parser = identity_subparser.add_parser(name='get', help='Get an identity')
        identity_get_parser.add_argument('--id',
                                         dest='id',
                                         type=int,
                                         required=True,
                                         help='The identity id')
        identity_get_parser.set_defaults(cmd=self.get)
        identity_create_parser = identity_subparser.add_parser(name='create', help='Create an identity')
        identity_create_parser.add_argument('-n', '--name',
                                            dest='name',
                                            type=str,
                                            required=True,
                                            help='The identity name')
        identity_create_parser.add_argument('--pubkey',
                                            dest='pubkey',
                                            type=pathlib.Path,
                                            required=True,
                                            help='Path to the SSH public key')
        identity_create_parser.set_defaults(cmd=self.create)
        identity_remove_parser = identity_subparser.add_parser(name='remove', help='Remove an identity')
        identity_remove_parser.add_argument('--id',
                                            dest='id',
                                            type=int,
                                            required=True,
                                            help='The identity id')
        identity_remove_parser.set_defaults(cmd=self.remove)


    def list(self, args: argparse.Namespace) -> int:    # pylint: disable=unused-argument
        identities = self.identity_controller.list()
        for identity in identities:
            console.print(f'- Id: {identity.identity_id}')
            console.print(f'  Name: {identity.name}')
        return 0

    def get(self, args: argparse.Namespace) -> int:
        identity = self.identity_controller.get(args.id)
        if not identity:
            console.print(f'ERROR: Identity with id {args.id} not found')
            return 1
        console.print(f'- Id: {identity.identity_id}')
        console.print(f'  Name: {identity.name}')
        return 0

    def create(self, args: argparse.Namespace) -> int:
        identity_path = args.pubkey.expanduser()
        with console.status(f'[magenta] Creating identity {args.name}') as status:
            if not identity_path.exists():
                status.update(f'ERROR: Public key at path {args.pubkey} does not exist')
                return 1
            identity = IdentityModel(name=args.name)
            with open(identity_path, 'r', encoding='UTF-8') as p:
                identity.public_key = p.read()
            status.update(f'Read public key from path {args.pubkey}')

            identity = self.identity_controller.create(identity)
            status.update(f'Created identity {identity.identity_id}: {identity.name}')
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        with console.status(f'[magenta] Removing identity {args.id}') as status:
            self.identity_controller.remove(args.id)
            status.update(f'Removed identity {args.id}')
        return 0
