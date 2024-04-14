import argparse
import uuid

from kaso_mashin import console
from kaso_mashin.cli.commands import BaseCommands
from kaso_mashin.common.config import Config
from kaso_mashin.common.entities import (
    BootstrapListSchema, BootstrapGetSchema, BootstrapCreateSchema, BootstrapModifySchema)


class BootstrapCommands(BaseCommands[BootstrapListSchema, BootstrapGetSchema]):
    """
    Implementation of the bootstrap command group
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self._prefix = '/api/bootstraps'
        self._list_schema_type = BootstrapListSchema
        self._get_schema_type = BootstrapGetSchema

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

    def create(self, args: argparse.Namespace) -> int:
        schema = BootstrapCreateSchema(name=args.name,
                                       kind=args.kind,
                                       content='<TODO>')
        resp = self._api_client(uri='/api/bootstraps/',
                                method='POST',
                                schema=schema,
                                expected_status=[201],
                                fallback_msg='Failed creating bootstrap')
        if not resp:
            return 1
        bootstrap = BootstrapGetSchema.model_validate(resp.content)
        console.print(bootstrap)
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = BootstrapModifySchema(name=args.name,
                                       kind=args.kind,
                                       content='<TODO>')
        resp = self._api_client(uri=f'/api/bootstraps/{args.uid}',
                                method='PUT',
                                schema=schema,
                                expected_status=[200],
                                fallback_msg='Failed to modify bootstrap')
        if not resp:
            return 1
        bootstrap = BootstrapGetSchema.model_validate(resp.content)
        console.print(bootstrap)


