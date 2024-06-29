import sys
import logging
import pathlib
import typing
import argparse

from kaso_mashin import __version__, console, default_config_file
from kaso_mashin.common.base_types import CLIArgumentsHolder
from kaso_mashin.common.config import Config
from kaso_mashin.cli.commands import (
    NetworkCommands,
    ImageCommands,
    IdentityCommands,
    InstanceCommands,
    BootstrapCommands,
)


def main(args: typing.Optional[typing.List] = None) -> int:
    """
    Main entry point for the CLI

    Returns
        An exit code. 0 when successful, non-zero otherwise
    """
    logger = logging.getLogger("kaso_mashin")
    config = Config()

    network_commands = NetworkCommands(config=config)
    image_commands = ImageCommands(config=config)
    identity_commands = IdentityCommands(config=config)
    bootstrap_commands = BootstrapCommands(config=config)
    instance_commands = InstanceCommands(config=config)

    parsed_args = CLIArgumentsHolder(config=config)
    parser = argparse.ArgumentParser(add_help=True, description=f"kaso-mashin - {__version__}")
    parser.add_argument("-d", "--debug", action="store_true", dest="debug", help="Debug")
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        type=pathlib.Path,
        required=False,
        default=parsed_args.config,
        help=f"Path to the configuration file. Defaults to {parsed_args.config}",
    )
    parser.add_argument(
        "--host",
        dest="default_server_host",
        type=str,
        required=False,
        default=parsed_args.host,
        help="The server host to communicate with",
    )
    parser.add_argument(
        "--port",
        dest="default_server_port",
        type=int,
        required=False,
        default=parsed_args.port,
        help="The server port to communicate with",
    )
    subparsers = parser.add_subparsers(dest="group")

    network_parser = subparsers.add_parser(name="network", help="Manage Networks")
    network_commands.register_commands(network_parser)
    image_parser = subparsers.add_parser(name="image", help="Manage Images")
    image_commands.register_commands(image_parser)
    identity_parser = subparsers.add_parser(name="identity", help="Manage Identities")
    identity_commands.register_commands(identity_parser)
    instance_parser = subparsers.add_parser(name="instance", help="Manage Instances")
    instance_commands.register_commands(instance_parser)
    bootstrap_parser = subparsers.add_parser(name="bootstrap", help="Manage Bootstraps")
    bootstrap_commands.register_commands(bootstrap_parser)

    parser.parse_args(args if args is not None else sys.argv[1:], namespace=parsed_args)
    logger.setLevel(logging.DEBUG if parsed_args.debug else logging.INFO)
    config.load(parsed_args.config)
    config.cli_override(parsed_args)
    try:
        if parsed_args.cmd is not None:
            return parsed_args.cmd(args)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        pass
    except Exception:
        console.print_exception()
    return 1


if __name__ == "__main__":
    sys.exit(main())
