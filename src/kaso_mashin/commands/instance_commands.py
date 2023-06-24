import argparse
import shutil
import pathlib

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import InstanceModel, VMScriptModel, BootstrapKind, NetworkKind


class InstanceCommands(AbstractCommands):
    """
    Implementation of instance command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        instance_subparser = parser.add_subparsers()
        instance_list_parser = instance_subparser.add_parser(name='list', help='List instances')
        instance_list_parser.set_defaults(cmd=self.list)
        instance_get_parser = instance_subparser.add_parser(name='get', help='Get an instance')
        instance_get_parser.add_argument('--id',
                                         dest='id',
                                         type=int,
                                         required=True,
                                         help='The instance id')
        instance_get_parser.set_defaults(cmd=self.get)
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
        instance_create_parser.add_argument('--network-id',
                                            dest='network_id',
                                            type=int,
                                            required=True,
                                            help='The network id on which this instance should be attached')
        instance_create_parser.add_argument('--image-id',
                                            dest='image_id',
                                            type=int,
                                            required=True,
                                            help='The image id containing the OS of this instance')
        instance_create_parser.add_argument('--identity-id',
                                            dest='identity_id',
                                            type=int,
                                            required=True,
                                            help='The identity id permitted to log in to this instance')
        instance_create_parser.add_argument('--static-ip4',
                                            dest='static_ip4',
                                            type=str,
                                            required=False,
                                            help='An optional static IP address')
        instance_create_parser.add_argument('-b', '--bootstrapper',
                                            dest='bootstrapper',
                                            type=str,
                                            choices=[k.value for k in list(BootstrapKind)],
                                            required=False,
                                            default=BootstrapKind.CI,
                                            help='The bootstrapper to use for this instance')
        instance_create_parser.add_argument('-s', '--size',
                                            dest='os_disk_size',
                                            type=str,
                                            required=False,
                                            default='5G',
                                            help='OS disk size, defaults to 5G')
        instance_create_parser.set_defaults(cmd=self.create)
        instance_remove_parser = instance_subparser.add_parser(name='remove', help='Remove an instance')
        instance_remove_parser.add_argument('--id',
                                            dest='id',
                                            type=int,
                                            required=True,
                                            help='The instance id')
        instance_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
        instances = self.instance_controller.list()
        for instance in instances:
            console.print(f'- Id:           {instance.instance_id}')
            console.print(f'  Name:         {instance.name}')
            console.print(f'  Path:         {instance.path}')
            console.print(f'  Image:        {instance.image.name}')
            console.print(f'  OS disk path: {instance.os_disk_path}')
            console.print(f'  Network:      {instance.network.name}')
            console.print(f'  Identity:     {instance.identity.name}')
        return 0

    def get(self, args: argparse.Namespace) -> int:
        instance = self.instance_controller.get(args.id)
        if not instance:
            console.print(f'ERROR: Instance with id {args.id} not found')
            return 1
        console.print(f'- Id: {instance.instance_id}')
        console.print(f'  Name: {instance.name}')
        console.print(f'  Path: {instance.path}')
        console.print(f'  Image: {instance.image.name}')
        console.print(f'  OS disk path: {instance.os_disk_path}')
        console.print(f'  Network:      {instance.network.name}')
        console.print(f'  Identity:     {instance.identity.name}')
        return 0

    def create(self, args: argparse.Namespace) -> int:
        with console.status(f'[magenta] Creating instance {args.name}') as status:
            network = self.network_controller.get(args.network_id)
            status.update(f'Found network {network.network_id}: {network.name}')

            image = self.image_controller.get(args.image_id)
            status.update(f'Found image {image.image_id}: {image.name}')

            identity = self.identity_controller.get(args.identity_id)
            status.update(f'Found identity {identity.identity_id}: {identity.name}')

            model = InstanceModel(name=args.name,
                                  vcpu=args.vcpu,
                                  ram=args.ram,
                                  os_disk_size=args.os_disk_size or self.config.default_os_disk_size,
                                  bootstrapper=args.bootstrapper,
                                  image=image,
                                  identity=identity,
                                  network=network)
            if args.static_ip4:
                model.static_ip4 = args.static_ip4
            model = self.instance_controller.create(model)
            status.update(f'Registered instance {model.instance_id}: {model.name} at path {model.path}')

            os_disk_path = pathlib.Path(model.os_disk_path)
            image_path = pathlib.Path(model.image.path)
            self.disk_controller.create(os_disk_path, image_path)
            status.update(f'Created OS disk with backing image {model.image.name}')

            self.disk_controller.resize(os_disk_path, model.os_disk_size)
            status.update(f'Resized OS disk to {model.os_disk_size}')

            self.bootstrap_controller.bootstrap(model)
            status.update(f'Created bootstrapper {model.bootstrapper}')

            vm_script_path = pathlib.Path(model.path).joinpath('vm.sh')
            VMScriptModel(model, vm_script_path)
            vm_script_path.chmod(0o755)
            status.update(f'Created VM script at {vm_script_path}')

            status.update(f'Start the instance using "sudo {vm_script_path} now')
            if model.network.kind == NetworkKind.VMNET_SHARED:
                status.update('Waiting for the instance to phone home')
                self.phonehome_controller.wait_for_instance(model=model)
                status.update('Instance phoned home')
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        with console.status(f'[magenta] Removing instance {args.id}') as status:
            instance = self.instance_controller.get(args.id)
            if not instance:
                status.update(f'ERROR: Instance {args.id} does not exist')
                return 1

            shutil.rmtree(instance.path)
            status.update(f'Removed instance path {instance.path}')

            self.instance_controller.remove(instance.instance_id)
            status.update(f'Removed instance {instance.instance_id}: {instance.name}')
        return 0
