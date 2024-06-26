import argparse
import pathlib
import uuid

import passlib.hash

from kaso_mashin import console
from kaso_mashin.cli.commands import BaseCommands
from kaso_mashin.common.config import Config
from kaso_mashin.common.entities import (
    IdentityListSchema,
    IdentityGetSchema,
    IdentityCreateSchema,
    IdentityModifySchema,
    IdentityKind,
)


class IdentityCommands(BaseCommands[IdentityListSchema, IdentityGetSchema]):
    """
    Implementation of the identity command group
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self._prefix = "/api/identities"
        self._list_schema_type = IdentityListSchema
        self._get_schema_type = IdentityGetSchema

    def register_commands(self, parser: argparse.ArgumentParser):
        identity_subparser = parser.add_subparsers()
        identity_list_parser = identity_subparser.add_parser(name="list", help="List identities")
        identity_list_parser.set_defaults(cmd=self.list)
        identity_get_parser = identity_subparser.add_parser(name="get", help="Get an identity")
        identity_get_parser.add_argument(
            "--uid", dest="uid", type=uuid.UUID, help="The identity uid"
        )
        identity_get_parser.set_defaults(cmd=self.get)
        identity_create_parser = identity_subparser.add_parser(
            name="create", help="Create an identity"
        )
        identity_create_parser.add_argument(
            "-n",
            "--name",
            dest="name",
            type=str,
            required=True,
            help="The identity name",
        )
        identity_create_pass_or_pubkey = identity_create_parser.add_mutually_exclusive_group(
            required=True
        )
        identity_create_pass_or_pubkey.add_argument(
            "--public-key",
            dest="pubkey",
            type=pathlib.Path,
            default=None,
            help="Path to the SSH public key for public key-type credentials",
        )
        identity_create_pass_or_pubkey.add_argument(
            "--password",
            dest="passwd",
            type=str,
            default=None,
            help="A password for password-type credentials",
        )
        identity_create_parser.add_argument(
            "--gecos",
            dest="gecos",
            type=str,
            required=False,
            help="An optional account GECOS to override the default",
        )
        identity_create_parser.add_argument(
            "--homedir",
            dest="homedir",
            type=str,
            required=False,
            help="An optional home directory to override the default",
        )
        identity_create_parser.add_argument(
            "--shell",
            dest="shell",
            type=str,
            required=False,
            help="An optional shell to override the default",
        )
        identity_create_parser.set_defaults(cmd=self.create)
        identity_modify_parser = identity_subparser.add_parser(
            name="modify", help="Modify an identity"
        )
        identity_modify_parser.add_argument(
            "--uid",
            dest="uid",
            type=uuid.UUID,
            required=True,
            help="The identity uid to modify",
        )
        identity_modify_parser.add_argument(
            "-n",
            "--name",
            dest="name",
            type=str,
            required=False,
            help="Name of the identity",
        )
        identity_modify_parser.add_argument(
            "--gecos",
            dest="gecos",
            type=str,
            required=False,
            default=None,
            help="An optional account GECOS to override the default",
        )
        identity_modify_parser.add_argument(
            "--homedir",
            dest="homedir",
            type=str,
            required=False,
            default=None,
            help="An optional home directory to override the default",
        )
        identity_modify_parser.add_argument(
            "--shell",
            dest="shell",
            type=str,
            required=False,
            default=None,
            help="An optional shell to override the default",
        )
        identity_modify_pass_or_pubkey = identity_modify_parser.add_mutually_exclusive_group(
            required=True
        )
        identity_modify_pass_or_pubkey.add_argument(
            "--public-key",
            dest="pubkey",
            type=pathlib.Path,
            default=None,
            help="Path to the SSH public key for public key-type credentials",
        )
        identity_modify_pass_or_pubkey.add_argument(
            "--password",
            dest="passwd",
            type=str,
            default=None,
            help="A password for password-type credentials",
        )
        identity_modify_parser.set_defaults(cmd=self.modify)
        identity_remove_parser = identity_subparser.add_parser(
            name="remove", help="Remove an identity"
        )
        identity_remove_parser.add_argument(
            "--uid",
            dest="uid",
            type=uuid.UUID,
            required=True,
            help="The identity uid to remove",
        )
        identity_remove_parser.set_defaults(cmd=self.remove)

    def create(self, args: argparse.Namespace) -> int:
        schema = IdentityCreateSchema(
            name=args.name,
            kind=IdentityKind.PUBKEY,
            gecos=args.gecos,
            homedir=args.homedir,
            shell=args.shell,
            credential="",
        )
        if not args.pubkey and not args.passwd:
            console.print(
                "[red]ERROR[/red]: You must either provide the path to a public key or a password"
            )
            return 1
        if args.pubkey:
            schema.kind = IdentityKind.PUBKEY
            pubkey_path = args.pubkey.expanduser()
            if not pubkey_path.exists():
                console.print(
                    f"[red]ERROR[/red]: Public key at path {args.pubkey_path} does not exist"
                )
                return 1
            with open(pubkey_path, "r", encoding="UTF-8") as p:
                schema.pubkey = p.readline().strip()
        else:
            schema.kind = IdentityKind.PASSWORD
            schema.passwd = passlib.hash.sha512_crypt.using(rounds=4096).hash(args.passwd)
        resp = self._api_client(
            uri=f"{self.prefix}/",
            method="POST",
            schema=schema,
            expected_status=[201],
            fallback_msg="Failed to create the identity",
        )
        if not resp:
            return 1
        identity = IdentityGetSchema.model_validate_json(resp.content)
        console.print(f"Created identity with id {identity.uid}")
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = IdentityModifySchema(
            name=args.name,
            kind=IdentityKind.PUBKEY,
            gecos=args.gecos,
            homedir=args.homedir,
            shell=args.shell,
            credential="",
        )
        if args.pubkey:
            pubkey_path = args.pubkey.expanduser()
            if not pubkey_path.exists():
                console.print(
                    f"[red]ERROR[/red]: Public key at path {args.pubkey_path} does not exist"
                )
                return 1
            with open(pubkey_path, "r", encoding="UTF-8") as p:
                schema.pubkey = p.read().strip()
        if args.passwd:
            schema.credential = passlib.hash.sha512_crypt.using(rounds=4096).hash(args.passwd)
        resp = self._api_client(
            uri=f"{self.prefix}/{args.uid}",
            method="PUT",
            schema=schema,
            expected_status=[200],
            fallback_msg="Failed to modify identity",
        )
        if not resp:
            return 1
        identity = IdentityGetSchema.model_validate_json(resp.content)
        console.print(identity)
        return 0
