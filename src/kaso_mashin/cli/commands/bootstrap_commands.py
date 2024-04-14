import argparse
import uuid

import rich.table
import rich.box

from kaso_mashin import console
from kaso_mashin.cli.commands import AbstractCommands
from kaso_mashin.common.entities import (
    BootstrapListSchema, BootstrapGetSchema, BootstrapCreateSchema, BootstrapModifySchema)


class BootstrapCommands(AbstractCommands):
    """
    Implementation of the bootstrap command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        bootstrap_subparser = parser.add_subparsers()
        bootstrap_list_parser = bootstrap_subparser.add_parser(name='list', help='List bootstraps')
        bootstrap_list_parser.set_defaults(cmd=self.list)
        bootstrap_get_parser = bootstrap_subparser.add_parser(name='get', help='Get bootstrap')
        bootstrap_get_parser.add_argument('--uid',
                                          dest='uid',
                                          type=uuid.UUID,
                                          help='The bootstrap uid')
        bootstrap_get_parser.set_defaults(cmd=self.get)
        bootstrap_create_parser = bootstrap_subparser.add_parser(name='create', help='Create bootstrap')
        bootstrap_create_parser.add_argument('-n', '--name',
                                             dest='name',
                                             type=str,
                                             required=True,
                                             help='The bootstrap name')
        bootstrap_create_parser.set_defaults(cmd=self.create)
        bootstrap_modify_parser = bootstrap_subparser.add_parser(name='modify', help='Modify bootstrap')
        bootstrap_modify_parser.add_argument('--uid',
                                             dest='uid',
                                             type=uuid.UUID,
                                             help='The bootstrap uid')
        bootstrap_modify_parser.set_defaults(cmd=self.modify)
        bootstrap_remove_parser = bootstrap_subparser.add_parser(name='remove', help='Remove a bootstrap')
        bootstrap_remove_parser.add_argument('--uid',
                                             dest='uid',
                                             type=uuid.UUID,
                                             help='The bootstrap uid')
        bootstrap_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:
        del args
        resp = self.api_client(uri='/api/bootstraps/',
                               expected_status=[200])
        if not resp:
            return 1
        bootstraps = [BootstrapListSchema.model_validate(bs) for bs in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]ID')
        table.add_column('[blue]Name')
        for bootstrap in bootstraps:
            table.add_row(str(bootstrap.uid), bootstrap.name)
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/bootstraps/{args.uid}',
                               expected_status=[200],
                               fallback_msg='Bootstrap not found')
        if not resp:
            return 1
        bootstrap = BootstrapGetSchema.model_validate_json(resp.content)
        self._print_bootstrap(bootstrap)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        schema = BootstrapCreateSchema(name=args.name,
                                              kind=args.kind,
                                              content='<TODO>')
        resp = self.api_client(uri='/api/bootstraps/',
                               method='POST',
                               schema=schema,
                               expected_status=[201],
                               fallback_msg='Failed creating bootstrap')
        if not resp:
            return 1
        bootstrap = BootstrapGetSchema.model_validate(resp.content)
        self._print_bootstrap(bootstrap)
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = BootstrapModifySchema(name=args.name,
                                       kind=args.kind,
                                       content='<TODO>')
        resp = self.api_client(uri=f'/api/bootstraps/{args.uid}',
                               method='PUT',
                               schema=schema,
                               expected_status=[200],
                               fallback_msg='Failed to modify bootstrap')
        if not resp:
            return 1
        bootstrap = BootstrapGetSchema.model_validate(resp.content)
        self._print_bootstrap(bootstrap)

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/bootstraps/{args.uid}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove bootstrap')
        if not resp:
            return 1
        if resp.status_code == 204:
            console.print(f'Removed bootstrap with id {args.uid}')
        elif resp.status_code == 404:
            console.print(f'Bootstrap with id {args.uid} does not exist')
        return 0

    @staticmethod
    def _print_bootstrap(bootstrap: BootstrapGetSchema):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]UID', str(bootstrap.uid))
        table.add_row('[blue]Name', bootstrap.name)
        table.add_row('[blue]Kind', bootstrap.kind)
        table.add_row('[blue]Required Keys', ','.join(bootstrap.required_keys))
        table.add_row('[blue]Content', bootstrap.content)
        console.print(table)
