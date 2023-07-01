import argparse
import pathlib

import rich.tree
import rich.table
import rich.columns

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import IdentityKind, IdentityModel


class IdentityCommands(AbstractCommands):
    """
    Implementation of the identity command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        identity_subparser = parser.add_subparsers()
        identity_list_parser = identity_subparser.add_parser(name='list', help='List identities')
        identity_list_parser.set_defaults(cmd=self.list)
        identity_get_parser = identity_subparser.add_parser(name='get', help='Get an identity')
        identity_get_id_or_name = identity_get_parser.add_mutually_exclusive_group(required=True)
        identity_get_id_or_name.add_argument('--id',
                                             dest='id',
                                             type=int,
                                             help='The identity id')
        identity_get_id_or_name.add_argument('--name',
                                             dest='name',
                                             type=str,
                                             help='The identity name')
        identity_get_parser.set_defaults(cmd=self.get)
        identity_create_parser = identity_subparser.add_parser(name='create', help='Create an identity')
        identity_create_parser.add_argument('-n', '--name',
                                            dest='name',
                                            type=str,
                                            required=True,
                                            help='The identity name')
        identity_create_parser.add_argument('-k', '--kind',
                                            dest='kind',
                                            type=str,
                                            required=False,
                                            choices=[k.value for k in list(IdentityKind)],
                                            help='The identity kind')
        identity_create_pass_or_pubkey = identity_create_parser.add_mutually_exclusive_group(required=True)
        identity_create_pass_or_pubkey.add_argument('--public-key',
                                                    dest='credentials',
                                                    type=pathlib.Path,
                                                    help='Path to the SSH public key for public key-type credentials')
        identity_create_pass_or_pubkey.add_argument('--password',
                                                    dest='credentials',
                                                    type=str,
                                                    help='A password for password-type credentials')
        identity_create_parser.set_defaults(cmd=self.create)
        identity_remove_parser = identity_subparser.add_parser(name='remove', help='Remove an identity')
        identity_remove_parser.add_argument('--id',
                                            dest='id',
                                            type=int,
                                            required=True,
                                            help='The identity id')
        identity_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
        identities = self.identity_controller.list()
        tree = rich.tree.Tree(label='Identities')
        for identity in identities:
            ntree = tree.add(label=f'{identity.identity_id}: {identity.name}')
            ntree.add(rich.columns.Columns(['Id:', str(identity.identity_id)]))
            ntree.add(rich.columns.Columns(['Name:', identity.name]))
            ntree.add(rich.columns.Columns(['Kind:', identity.kind.value]))
            match identity.kind:
                case IdentityKind.PASSWORD:
                    ntree.add(rich.columns.Columns(['Credential:', '**MASKED**']))
                case IdentityKind.PUBKEY:
                    ntree.add(rich.columns.Columns(['Credential:', identity.credentials]))
            console.print(tree)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        identity = self.identity_controller.get(identity_id=args.id, name=args.name)
        if not identity:
            console.print(f'ERROR: Identity with id {args.id} not found')
            return 1
        console.print(f'- Id: {identity.identity_id}')
        console.print(f'  Name: {identity.name}')
        console.print(f'  Kind: {identity.kind.value}')
        return 0

    def create(self, args: argparse.Namespace) -> int:
        if args.kind == IdentityKind.PUBKEY.value:
            pubkey_path = args.credentials.expanduser()
            if not pubkey_path.exists():
                console.print(f'[red]ERROR[/red]: Public key at path {args.pubkey_path} does not exist')
                return 1
            with open(pubkey_path, 'r', encoding='UTF-8') as p:
                credentials = p.read().strip()
        else:
            credentials = args.password

        identity = IdentityModel(name=args.name,
                                 kind=IdentityKind(args.kind),
                                 credentials=credentials)
        identity = self.identity_controller.create(identity)
        console.print(f'Created identity {identity.identity_id}: {identity.name}')
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        with console.status(f'[magenta] Removing identity {args.id}') as status:
            self.identity_controller.remove(args.id)
            status.update(f'Removed identity {args.id}')
        return 0
