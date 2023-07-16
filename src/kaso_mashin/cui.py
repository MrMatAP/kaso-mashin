import sys
import pathlib
import typing
import argparse

from kaso_mashin import __version__, console, default_config_file
from kaso_mashin.config import Config
from kaso_mashin.db import DB
from kaso_mashin.runtime import Runtime
from kaso_mashin.commands import (
    NetworkCommands, ImageCommands, IdentityCommands, BootstrapCommands, InstanceCommands,
    ServerCommands
)


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the CLI

    Returns
        An exit code. 0 when successful, non-zero otherwise
    """
    config = Config(config_file=default_config_file)
    db = DB(config)
    runtime = Runtime(config=config, db=db)
    network_commands = NetworkCommands(runtime)
    image_commands = ImageCommands(runtime)
    identity_commands = IdentityCommands(runtime)
    bootstrap_commands = BootstrapCommands(runtime)
    instance_commands = InstanceCommands(runtime)
    server_commands = ServerCommands(runtime)

    parser = argparse.ArgumentParser(add_help=True, description=f'kaso-mashin - {__version__}')
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', help='Silent operation')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug')
    parser.add_argument('-c', '--config',
                        dest='config',
                        type=pathlib.Path,
                        required=False,
                        default=default_config_file,
                        help=f'Path to the configuration file. Defaults to {default_config_file}')
    parser.add_argument('-p', '--path',
                        dest='path',
                        type=pathlib.Path,
                        required=False,
                        default=config.path,
                        help=f'Cloud directory. Defaults to {config.path}')
    subparsers = parser.add_subparsers(dest='group')

    network_parser = subparsers.add_parser(name='network', help='Manage Networks')
    network_commands.register_commands(network_parser)
    image_parser = subparsers.add_parser(name='image', help='Manage images')
    image_commands.register_commands(image_parser)
    identity_parser = subparsers.add_parser(name='identity', help='Manage identities')
    identity_commands.register_commands(identity_parser)
    bootstrap_parser = subparsers.add_parser(name='bootstrap', help='Manage bootstrap')
    bootstrap_commands.register_commands(bootstrap_parser)
    instance_parser = subparsers.add_parser(name='instance', help='Manage instances')
    instance_commands.register_commands(instance_parser)
    server_parser = subparsers.add_parser(name='server', help='Start the Kaso Mashin server')
    server_commands.register_commands(server_parser)

    args = parser.parse_args(args if args is not None else sys.argv[1:])
    if args.config:
        config.config_file = args.config
    if not args.path.exists():
        console.print(f'Creating directory at {args.path}')
        args.path.mkdir(parents=True)
    config.path = args.path
    runtime.late_init()
    try:
        if hasattr(args, 'cmd'):
            return args.cmd(args)
        else:
            parser.print_help()
    except Exception as ex:       # pylint: disable=broad-except
        console.print_exception()
    return 1


if __name__ == '__main__':
    sys.exit(main())
