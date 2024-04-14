import argparse
import pathlib
import uuid

import passlib.hash
import rich.table
import rich.box
import rich.tree

from kaso_mashin import console
from kaso_mashin.cli.commands import AbstractCommands
from kaso_mashin.common.entities import (
    IdentityListSchema, IdentityGetSchema, IdentityCreateSchema, IdentityModifySchema,
    IdentityKind
)


class IdentityCommands(AbstractCommands):
    """
    Implementation of the identity command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        identity_subparser = parser.add_subparsers()
        identity_list_parser = identity_subparser.add_parser(name='list', help='List identities')
        identity_list_parser.set_defaults(cmd=self.list)
        identity_get_parser = identity_subparser.add_parser(name='get', help='Get an identity')
        identity_get_parser.add_argument('--uid',
                                         dest='uid',
                                         type=uuid.UUID,
                                         help='The identity uid')
        identity_get_parser.set_defaults(cmd=self.get)
        identity_create_parser = identity_subparser.add_parser(name='create', help='Create an identity')
        identity_create_parser.add_argument('-n', '--name',
                                            dest='name',
                                            type=str,
                                            required=True,
                                            help='The identity name')
        identity_create_pass_or_pubkey = identity_create_parser.add_mutually_exclusive_group(required=True)
        identity_create_pass_or_pubkey.add_argument('--public-key',
                                                    dest='pubkey',
                                                    type=pathlib.Path,
                                                    default=None,
                                                    help='Path to the SSH public key for public key-type credentials')
        identity_create_pass_or_pubkey.add_argument('--password',
                                                    dest='passwd',
                                                    type=str,
                                                    default=None,
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
        identity_modify_parser.add_argument('--uid',
                                            dest='uid',
                                            type=uuid.UUID,
                                            required=True,
                                            help='The identity uid to modify')
        identity_modify_parser.add_argument('-n', '--name',
                                            dest='name',
                                            type=str,
                                            required=False,
                                            help='Name of the identity')
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
        identity_modify_pass_or_pubkey = identity_modify_parser.add_mutually_exclusive_group(required=True)
        identity_modify_pass_or_pubkey.add_argument('--public-key',
                                                    dest='pubkey',
                                                    type=pathlib.Path,
                                                    default=None,
                                                    help='Path to the SSH public key for public key-type credentials')
        identity_modify_pass_or_pubkey.add_argument('--password',
                                                    dest='passwd',
                                                    type=str,
                                                    default=None,
                                                    help='A password for password-type credentials')
        identity_modify_parser.set_defaults(cmd=self.modify)
        identity_remove_parser = identity_subparser.add_parser(name='remove', help='Remove an identity')
        identity_remove_parser.add_argument('--uid',
                                            dest='uid',
                                            type=uuid.UUID,
                                            required=True,
                                            help='The identity uid to remove')
        identity_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:
        del args
        resp = self.api_client(uri='/api/identities/', expected_status=[200])
        if not resp:
            return 1
        identities = [IdentityListSchema.model_validate(identity) for identity in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]UID')
        table.add_column('[blue]Name')
        table.add_column('[blue]Kind')
        table.add_column('[blue]GECOS')
        for identity in identities:
            table.add_row(str(identity.uid), identity.name, identity.kind, identity.gecos)
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/identities/{args.uid}',
                               expected_status=[200],
                               fallback_msg=f'Identity with id {args.uid} could not be found')
        if not resp:
            return 1
        identity = IdentityGetSchema.model_validate_json(resp.content)
        self._print_identity(identity)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        schema = IdentityCreateSchema(name=args.name,
                                      kind=IdentityKind.PUBKEY,
                                      gecos=args.gecos,
                                      homedir=args.homedir,
                                      shell=args.shell,
                                      credential='')
        if not args.pubkey and not args.passwd:
            console.print('[red]ERROR[/red]: You must either provide the path to a public key or a password')
            return 1
        if args.pubkey:
            schema.kind = IdentityKind.PUBKEY
            pubkey_path = args.pubkey.expanduser()
            if not pubkey_path.exists():
                console.print(f'[red]ERROR[/red]: Public key at path {args.pubkey_path} does not exist')
                return 1
            with open(pubkey_path, 'r', encoding='UTF-8') as p:
                schema.pubkey = p.readline().strip()
        else:
            schema.kind = IdentityKind.PASSWORD
            schema.passwd = passlib.hash.sha512_crypt.using(rounds=4096).hash(args.passwd)
        resp = self.api_client(uri='/api/identities/',
                               method='POST',
                               schema=schema,
                               expected_status=[201],
                               fallback_msg='Failed to create the identity')
        if not resp:
            return 1
        identity = IdentityGetSchema.model_validate_json(resp.content)
        console.print(f'Created identity with id {identity.uid}')
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = IdentityModifySchema(name=args.name,
                                      kind=IdentityKind.PUBKEY,
                                      gecos=args.gecos,
                                      homedir=args.homedir,
                                      shell=args.shell,
                                      credential='')
        if args.pubkey:
            pubkey_path = args.pubkey.expanduser()
            if not pubkey_path.exists():
                console.print(f'[red]ERROR[/red]: Public key at path {args.pubkey_path} does not exist')
                return 1
            with open(pubkey_path, 'r', encoding='UTF-8') as p:
                schema.pubkey = p.read().strip()
        if args.passwd:
            schema.passwd = passlib.hash.sha512_crypt.using(rounds=4096).hash(args.passwd)
        resp = self.api_client(uri=f'/api/identities/{args.uid}',
                               method='PUT',
                               schema=schema,
                               expected_status=[200],
                               fallback_msg='Failed to modify identity')
        if not resp:
            return 1
        identity = IdentityGetSchema.model_validate_json(resp.content)
        self._print_identity(identity)
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/identities/{args.uid}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove identity')
        if not resp:
            return 1
        if resp.status_code == 204:
            console.print(f'Removed identity with id {args.uid}')
        elif resp.status_code == 410:
            console.print(f'Identity with id {args.uid} does not exist')
        return 0 if resp else 1

    @staticmethod
    def _print_identity(identity: IdentityGetSchema):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]UID', str(identity.uid))
        table.add_row('[blue]Name', identity.name)
        table.add_row('[blue]Kind', identity.kind)
        table.add_row('[blue]GECOS', identity.gecos or '')
        table.add_row('[blue]Home Directory', str(identity.homedir) or '')
        table.add_row('[blue]Shell', identity.shell or '')
        table.add_row('[blue]Credential', identity.credential or '')
        console.print(table)
