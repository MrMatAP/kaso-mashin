import os.path
import sys
import typing
import argparse
from configparser import ConfigParser
import inspect

from mrmat_playground import __version__, console, default_config
from mrmat_playground.cloud_init_commands import CloudInitCommands
from mrmat_playground.instance_commands import InstanceCommands


def validate_config(config):
    """
    Validate or initialise our configuration
    """
    playground_path = config['DEFAULT']['playground_path']
    if not os.path.exists(playground_path):
        console.log(f'Creating playground path at {playground_path}')
        os.makedirs(playground_path)


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the CLI

    Returns
        An exit code. 0 when successful, non-zero otherwise
    """
    parser = argparse.ArgumentParser(add_help=True, description=f'{__name__} - {__version__}')
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', help='Silent operation')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug')
    parser.add_argument('-c', '--config', dest='config', help='Configuration file')
    subparsers = parser.add_subparsers(dest='group')

    cloud_init_parser = subparsers.add_parser(name='cloud-init', help='Manage Cloud-init configurations')
    cloud_init_subparser = cloud_init_parser.add_subparsers()
    cloud_init_create_parser = cloud_init_subparser.add_parser(name='create', help='Create a cloud-init configuration')
    cloud_init_create_parser.add_argument('-n', '--name',
                                          type=str,
                                          required=True,
                                          help='The cloud-init configuration name')
    cloud_init_create_parser.set_defaults(cmd=CloudInitCommands.create)
    cloud_init_remove_parser = cloud_init_subparser.add_parser(name='remove', help='Remove a cloud-init configuration')
    cloud_init_remove_parser.add_argument('-n', '--name',
                                          type=str,
                                          required=True,
                                          help='The cloud-init configuration name')
    cloud_init_remove_parser.set_defaults(cmd=CloudInitCommands.remove)

    instance_parser = subparsers.add_parser(name='instance', help='Manage Instances')
    instance_subparser = instance_parser.add_subparsers()
    instance_create_parser = instance_subparser.add_parser(name='create', help='Create an instance')
    instance_create_parser.add_argument('-n', '--name',
                                        dest='name',
                                        type=str,
                                        required=True,
                                        help='The instance name')
    instance_create_parser.add_argument('-s', '--size',
                                        dest='os_disk_size',
                                        type=str,
                                        required=False,
                                        default='5G',
                                        help='OS disk size, defaults to 5G')
    instance_create_parser.set_defaults(cmd=InstanceCommands.create)
    instance_remove_parser = instance_subparser.add_parser(name='remove', help='Remove an instance')
    instance_remove_parser.add_argument('-n', '--name',
                                        dest='name',
                                        type=str,
                                        required=True,
                                        help='The instance name')
    instance_remove_parser.set_defaults(cmd=InstanceCommands.remove)

    args = parser.parse_args(args if args is not None else sys.argv[1:])

    config = ConfigParser(strict=True, defaults=default_config)
    if args.config:
        config.read(args.config)
    validate_config(config)

    try:
        if hasattr(args, 'cmd'):
            # This may be simplified to just args.cmd(args, config) if you don't use command classes
            return args.cmd(args, config)() if inspect.isclass(args.cmd) else args.cmd(args, config)
        elif hasattr(args, 'group'):
            subparser = subparsers.choices.get(args.group)
            subparser.print_help() if subparser else parser.print_help()  # pylint: disable=W0106
        else:
            parser.print_help()
    except Exception:
        console.print_exception()
    return 1


if __name__ == '__main__':
    sys.exit(main())
