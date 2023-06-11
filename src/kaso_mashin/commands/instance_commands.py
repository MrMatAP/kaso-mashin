import argparse
import shutil
import pathlib
import typing
from http.server import HTTPServer, BaseHTTPRequestHandler

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import InstanceModel, VMScriptModel
from kaso_mashin.controllers import (
    NetworkController, ImageController, DiskController, IdentityController, InstanceController
)


class PhoneHomeServer(HTTPServer):
    """
    A small server waiting for an instance to call home. We override this to pass it a function to be called
    with the actual IP address the instance has. We can't do this in the handler because it is statically
    referred to by the PhoneHomeServer
    """

    def __init__(self,
                 server_address: tuple[str, int],
                 RequestHandlerClass: typing.Callable,
                 callback: typing.Callable,
                 bind_and_activate: bool = ...) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self._callback = callback

    @property
    def callback(self):
        return self._callback


class PhoneHomeHandler(BaseHTTPRequestHandler):
    """
    A handler for instances calling their mum
    """

    # It is actually required to be called do_POST, despite pylint complaining about it
    def do_POST(self):              # pylint: disable=invalid-name
        self.server.callback(self.client_address[0])
        self.send_response(code=200, message='Well, hello there!')
        self.end_headers()


class InstanceCommands(AbstractCommands):
    """
    Implementation of instance commands
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

    def list(self, args: argparse.Namespace) -> int:
        instance_controller = InstanceController(config=self.config, db=self.db)
        instances = instance_controller.list()
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
        instance_controller = InstanceController(config=self.config, db=self.db)
        instance = instance_controller.get(args.id)
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
        network_controller = NetworkController(config=self.config, db=self.db)
        image_controller = ImageController(config=self.config, db=self.db)
        disk_controller = DiskController(config=self.config, db=self.db)
        identity_controller = IdentityController(config=self.config, db=self.db)
        instance_controller = InstanceController(config=self.config, db=self.db)
        with console.status(f'[magenta] Creating instance {args.name}') as status:
            network = network_controller.get(args.network_id)
            status.update(f'Found network {network.network_id}: {network.name}')

            image = image_controller.get(args.image_id)
            status.update(f'Found image {image.image_id}: {image.name}')

            identity = identity_controller.get(args.identity_id)
            status.update(f'Found identity {identity.identity_id}: {identity.name}')

            instance = InstanceModel(name=args.name,
                                     vcpu=args.vcpu,
                                     ram=args.ram,
                                     os_disk_size=args.os_disk_size or self.config.default_os_disk_size,
                                     image=image,
                                     identity=identity,
                                     network=network)
            instance = instance_controller.create(instance)
            status.update(f'Registered instance {instance.instance_id}: {instance.name} at path {instance.path}')

            os_disk_path = pathlib.Path(instance.os_disk_path)
            image_path = pathlib.Path(instance.image.path)
            disk_controller.create(os_disk_path, image_path)
            status.update(f'Created OS disk with backing image {instance.image.name}')

            disk_controller.resize(os_disk_path, instance.os_disk_size)
            status.update(f'Resized OS disk to {instance.os_disk_size}')

            vm_script_path = pathlib.Path(instance.path).joinpath('vm.sh')
            VMScriptModel(instance, vm_script_path)
            status.update(f'Created VM script at {vm_script_path}')

        return 0


        # instance.metadata = CIMetadata(instance.instance_id, args.name)
        # instance.userdata = CIUserData(phone_home_url=f'http://{cloud.host_ip4}:{cloud.ph_port}/$INSTANCE_ID',
        #                                pubkey=cloud.public_key)
        # instance.userdata.admin_password = cloud.admin_password
        # instance.vendordata = CIVendorData()
        # instance.network_config = CINetworkConfig(mac=instance.mac,
        #                                           ipv4=args.ip,
        #                                           nm4=cloud.host_nm4,
        #                                           gw4=cloud.host_gw4,
        #                                           ns4=cloud.host_ns4)
        # instance.create()
        #
        # status.update('Waiting for the instance to phone home')
        # httpd = PhoneHomeServer(server_address=(cloud.host_ip4, cloud.ph_port),
        #                         callback=instance.configure,
        #                         RequestHandlerClass=PhoneHomeHandler)
        # httpd.timeout = 120
        # httpd.handle_request()

    def remove(self, args: argparse.Namespace) -> int:
        instance_controller = InstanceController(config=self.config, db=self.db)
        with console.status(f'[magenta] Removing instance {args.id}') as status:
            instance = instance_controller.get(args.id)
            if not instance:
                status.update(f'ERROR: Instance {args.id} does not exist')
                return 1

            shutil.rmtree(instance.path)
            status.update(f'Removed instance path {instance.path}')

            instance_controller.remove(instance.instance_id)
            status.update(f'Removed instance {instance.instance_id}: {instance.name}')
        return 0
