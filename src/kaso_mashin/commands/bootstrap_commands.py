import argparse

from kaso_mashin.commands import AbstractCommands


class BootstrapCommands(AbstractCommands):
    """
    Implementation of the bootstrap command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        bootstrap_subparser = parser.add_subparsers()
        bootstrap_create_ci_disk_parser = bootstrap_subparser.add_parser(name='list',
                                                                         help='(Re-)create a CI disk')
        bootstrap_create_ci_disk_parser.add_argument('--id',
                                                     dest='id',
                                                     type=int,
                                                     required=True,
                                                     help='The instance id')
        bootstrap_create_ci_disk_parser.set_defaults(cmd=self.create_ci_disk)

    def create_ci_disk(self, args: argparse.Namespace) -> int:
        instance = self.instance_controller.get(args.id)
        self.bootstrap_controller.create_ci_image(model=instance, ci_path=instance.ci_disk_path)
        return 0
