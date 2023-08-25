import sys
import logging
import pathlib
import typing
import argparse

from kaso_mashin import __version__, console, default_config_file
from kaso_mashin.common.config import Config
from kaso_mashin.cli.commands import (
    NetworkCommands, ImageCommands, IdentityCommands, InstanceCommands
)


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the CLI

    Returns
        An exit code. 0 when successful, non-zero otherwise
    """
    logger = logging.getLogger('kaso_mashin')
    config = Config()
    network_commands = NetworkCommands(config)
    image_commands = ImageCommands(config)
    identity_commands = IdentityCommands(config)
    instance_commands = InstanceCommands(config)

    parser = argparse.ArgumentParser(add_help=True, description=f'kaso-mashin - {__version__}')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug')
    parser.add_argument('-c', '--config',
                        dest='config',
                        type=pathlib.Path,
                        required=False,
                        default=default_config_file,
                        help=f'Path to the configuration file. Defaults to {default_config_file}')
    parser.add_argument('--host',
                        dest='default_server_host',
                        type=str,
                        required=False,
                        default=config.default_server_host,
                        help='The server host to communicate with')
    parser.add_argument('--port',
                        dest='default_server_port',
                        type=int,
                        required=False,
                        default=config.default_server_port,
                        help='The server port to communicate with')
    subparsers = parser.add_subparsers(dest='group')

    network_parser = subparsers.add_parser(name='network', help='Manage Networks')
    network_commands.register_commands(network_parser)
    image_parser = subparsers.add_parser(name='image', help='Manage images')
    image_commands.register_commands(image_parser)
    identity_parser = subparsers.add_parser(name='identity', help='Manage identities')
    identity_commands.register_commands(identity_parser)
    instance_parser = subparsers.add_parser(name='instance', help='Manage instances')
    instance_commands.register_commands(instance_parser)

    args = parser.parse_args(args if args is not None else sys.argv[1:])
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    config.load(args.config)
    config.cli_override(args)
    try:
        if hasattr(args, 'cmd'):
            return args.cmd(args)
        else:
            parser.print_help()
    except Exception:       # pylint: disable=broad-except
        console.print_exception()
    return 1


if __name__ == '__main__':
    sys.exit(main())
