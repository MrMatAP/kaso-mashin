import argparse
import pathlib

import rich.table
import rich.box
import rich.tree

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import IdentityKind, IdentitySchema, IdentityCreateSchema, IdentityModifySchema


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
                                             dest='identity_id',
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
                                            choices=[k.value for k in IdentityKind],
                                            help='The identity kind')
        identity_create_pass_or_pubkey = identity_create_parser.add_mutually_exclusive_group(required=True)
        identity_create_pass_or_pubkey.add_argument('--public-key',
                                                    dest='pubkey',
                                                    type=pathlib.Path,
                                                    help='Path to the SSH public key for public key-type credentials')
        identity_create_pass_or_pubkey.add_argument('--password',
                                                    dest='passwd',
                                                    type=str,
                                                    help='A password for password-type credentials')
        identity_create_parser.add_argument('--gecos',
                                            dest='gecos',
                                            type=str,
                                            required=False,
                                            help='An optional account GECOS to override the default')
        identity_create_parser.add_argument('--homedir',
                                            dest='homedir',
                                            type=str,
                                            required=False,
                                            help='An optional home directory to override the default')
        identity_create_parser.add_argument('--shell',
                                            dest='shell',
                                            type=str,
                                            required=False,
                                            help='An optional shell to override the default')
        identity_create_parser.set_defaults(cmd=self.create)
        identity_modify_parser = identity_subparser.add_parser(name='modify', help='Modify an identity')
        identity_modify_parser.add_argument('--id',
                                            dest='identity_id',
                                            type=int,
                                            required=True,
                                            help='The identity id to modify')
        identity_modify_parser.add_argument('--gecos',
                                            dest='gecos',
                                            type=str,
                                            required=False,
                                            default=None,
                                            help='An optional account GECOS to override the default')
        identity_modify_parser.add_argument('--homedir',
                                            dest='homedir',
                                            type=str,
                                            required=False,
                                            default=None,
                                            help='An optional home directory to override the default')
        identity_modify_parser.add_argument('--shell',
                                            dest='shell',
                                            type=str,
                                            required=False,
                                            default=None,
                                            help='An optional shell to override the default')
        identity_modify_parser.add_argument('--public-key',
                                            dest='pubkey',
                                            type=pathlib.Path,
                                            required=False,
                                            default=None,
                                            help='Path to the SSH public key for public key-type credentials')
        identity_modify_parser.add_argument('--password',
                                            dest='passwd',
                                            type=str,
                                            required=False,
                                            default=None,
                                            help='A password for password-type credentials')
        identity_modify_parser.set_defaults(cmd=self.modify)
        identity_remove_parser = identity_subparser.add_parser(name='remove', help='Remove an identity')
        identity_remove_parser.add_argument('--id',
                                            dest='identity_id',
                                            type=int,
                                            required=True,
                                            help='The identity id to remove')
        identity_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri='/api/identities/', expected_status=[200])
        if not resp:
            return 1
        identities = [IdentitySchema.model_validate(identity) for identity in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]ID')
        table.add_column('[blue]Kind')
        table.add_column('[blue]Name')
        for identity in identities:
            table.add_row(str(identity.identity_id), identity.name, str(identity.kind))
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/identities/{args.identity_id}',
                               expected_status=[200],
                               fallback_msg=f'Identity with id {args.identity_id} could not be found')
        if not resp:
            return 1
        identity = IdentitySchema.model_validate_json(resp.content)
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]Id', str(identity.identity_id))
        table.add_row('[blue]Name', identity.name)
        table.add_row('[blue]Kind', str(identity.kind))
        table.add_row('[blue]GECOS', identity.gecos or '')
        table.add_row('[blue]Home Directory', identity.homedir or '')
        table.add_row('[blue]Shell', identity.shell or '')
        table.add_row('[blue]Password', identity.passwd or '')
        table.add_row('[blue]Public Key', identity.pubkey or '')
        console.print(table)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        schema = IdentityCreateSchema(name=args.name,
                                      kind=args.kind,
                                      gecos=args.gecos,
                                      homedir=args.homedir,
                                      shell=args.shell)
        if args.kind == IdentityKind.PUBKEY.value:
            pubkey_path = args.pubkey.expanduser()
            if not pubkey_path.exists():
                console.print(f'[red]ERROR[/red]: Public key at path {args.pubkey_path} does not exist')
                return 1
            with open(pubkey_path, 'r', encoding='UTF-8') as p:
                schema.pubkey = p.read().strip()
        else:
            # TODO: Hash this right here
            schema.passwd = args.passwd

        resp = self.api_client(uri='/api/identities/',
                               method='POST',
                               body=schema.model_dump(),
                               expected_status=[201],
                               fallback_msg='Failed to create the identity')
        if not resp:
            return 1
        identity = IdentitySchema.model_validate_json(resp.content)
        console.print(f'Created identity with id {identity.identity_id}')
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = IdentityModifySchema(gecos=args.gecos,
                                      homedir=args.homedir,
                                      shell=args.shell)
        if args.pubkey:
            pubkey_path = args.pubkey.expanduser()
            if not pubkey_path.exists():
                console.print(f'[red]ERROR[/red]: Public key at path {args.pubkey_path} does not exist')
                return 1
            with open(pubkey_path, 'r', encoding='UTF-8') as p:
                schema.pubkey = p.read().strip()
        else:
            # TODO: Hash this right here
            schema.passwd = args.passwd

        resp = self.api_client(uri=f'/api/identities/{args.identity_id}',
                               method='PUT',
                               body=schema.model_dump(),
                               expected_status=[200],
                               fallback_msg='Failed to modify identity')
        return 0 if resp else 1

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/identities/{args.identity_id}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove identity')
        return 0 if resp else 1
