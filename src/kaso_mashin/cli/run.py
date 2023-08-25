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
    logger = logging.getLogger(__name__)
    config = Config(config_file=default_config_file)
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
    # TODO: We should keep this in the config file alone
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
    instance_parser = subparsers.add_parser(name='instance', help='Manage instances')
    instance_commands.register_commands(instance_parser)

    args = parser.parse_args(args if args is not None else sys.argv[1:])
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    logger.debug('Parsed commands')
    if args.config:
        config.config_file = args.config
    # TODO: We should not do this here
    if not args.path.exists():
        console.print(f'Creating directory at {args.path}')
        args.path.mkdir(parents=True)
    config.path = args.path
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
