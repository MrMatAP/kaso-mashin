import os.path
import sys
import typing
import argparse
from configparser import ConfigParser
import inspect

from mrmat_playground import __version__, console, default_config
from mrmat_playground.commands import CloudCommands, ImageCommands, InstanceCommands


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
    parser.add_argument('-p', '--path',
                        dest='path',
                        required=False,
                        default=os.path.expanduser(os.path.join('~', 'var', 'mrmat-playground')),
                        help='Cloud playground root directory')
    subparsers = parser.add_subparsers(dest='group')

    cloud_parser = subparsers.add_parser(name='cloud', help='Manage Clouds')
    cloud_subparser = cloud_parser.add_subparsers()
    cloud_get_parser = cloud_subparser.add_parser(name='get', help='Get a local cloud')
    cloud_get_parser.set_defaults(cmd=CloudCommands.get)
    cloud_create_parser = cloud_subparser.add_parser(name='create', help='Create a local cloud')
    cloud_create_parser.add_argument('-n', '--name',
                                     type=str,
                                     dest='name',
                                     required=True,
                                     help='The cloud name')
    cloud_create_parser.add_argument('--admin-password',
                                     type=str,
                                     dest='admin_password',
                                     required=True,
                                     help='An admin password to log in at the console')
    cloud_create_parser.add_argument('--ssh-public-key',
                                     dest='public_key_path',
                                     required=True,
                                     help='Path to a SSH public key')
    cloud_create_parser.add_argument('--host-if',
                                     dest='host_if',
                                     required=True,
                                     help='Name of the host interface (e.g. vlan1)')
    cloud_create_parser.add_argument('--host-ip4',
                                     dest='host_ip4',
                                     required=True,
                                     help='IPv4 address of the host interface')
    cloud_create_parser.add_argument('--host-nm4',
                                     dest='host_nm4',
                                     required=True,
                                     help='IPv4 netmask of the host interface')
    cloud_create_parser.add_argument('--host-gw4',
                                     dest='host_gw4',
                                     required=True,
                                     help='IPv4 default gateway of the host interface')
    cloud_create_parser.add_argument('--host-ns4',
                                     dest='host_ns4',
                                     required=True,
                                     help='IPv4 nameserver')
    cloud_create_parser.add_argument('--ph-port',
                                     type=int,
                                     dest='ph_port',
                                     required=False,
                                     default=10300,
                                     help='Port to listen on for the temporary phone-home server')
    cloud_create_parser.set_defaults(cmd=CloudCommands.create)

    image_parser = subparsers.add_parser(name='image', help='Manage images')
    image_subparser = image_parser.add_subparsers()
    image_download_parser = image_subparser.add_parser(name='download', help='Download images')
    image_download_parser.add_argument('-n', '--name',
                                       dest='name',
                                       type=str,
                                       choices=ImageCommands.IMAGE_URLS,
                                       required=True,
                                       help='The image to download')
    image_download_parser.set_defaults(cmd=ImageCommands.download)

    instance_parser = subparsers.add_parser(name='instance', help='Manage instances')
    instance_subparser = instance_parser.add_subparsers()
    instance_create_parser = instance_subparser.add_parser(name='create', help='Create an instance')
    instance_create_parser.add_argument('-n', '--name',
                                        dest='name',
                                        type=str,
                                        required=True,
                                        help='The instance name')
    instance_create_parser.add_argument('--vcpu',
                                        dest='vcpu',
                                        type=int,
                                        required=False,
                                        default=2,
                                        help='Number of vCPUs to assign to this instance')
    instance_create_parser.add_argument('--ram',
                                        dest='ram',
                                        type=int,
                                        required=False,
                                        default=2048,
                                        help='Amount of RAM in MB to assign to this instance')
    instance_create_parser.add_argument('--ip',
                                        dest='ip',
                                        type=str,
                                        required=True,
                                        help='The static IP address of the instance')
    instance_create_parser.add_argument('-s', '--size',
                                        dest='os_disk_size',
                                        type=str,
                                        required=False,
                                        default='5G',
                                        help='OS disk size, defaults to 5G')
    instance_create_parser.add_argument('--os',
                                        dest='os',
                                        type=str,
                                        choices=ImageCommands.IMAGE_URLS,
                                        required=False,
                                        default='ubuntu-jammy',
                                        help='The instance OS')
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

    try:
        if hasattr(args, 'cmd'):
            # This may be simplified to just args.cmd(args, config) if you don't use command classes
            return args.cmd(args, config)() if inspect.isclass(args.cmd) else args.cmd(args, config)
        else:
            parser.print_help()
    except Exception:
        console.print_exception()
    return 1


if __name__ == '__main__':
    sys.exit(main())
