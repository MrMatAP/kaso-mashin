import shutil
import argparse
import configparser
import typing
from http.server import HTTPServer, BaseHTTPRequestHandler

from mrmat_playground import console
from mrmat_playground.model import Cloud, Instance, CIMetadata, CINetworkConfig, CIUserData, CIVendorData


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


class InstanceCommands:
    """
    Implementation of instance commands
    """

    @staticmethod
    def create(args: argparse.Namespace, config: configparser.ConfigParser) -> int:
        with console.status(f'[magenta] Creating instance {args.name}') as status:
            cloud = Cloud(path=args.path)
            cloud.load()

            instance = Instance(path=cloud.instances_path.joinpath(args.name),
                                name=args.name)
            instance.backing_disk_path = cloud.images_path.joinpath(f'{args.os}.qcow2')
            instance.os_disk_size = args.os_disk_size or config['DEFAULT']['default_os_disk_size']
            instance.public_key = cloud.public_key

            (instance.instance_id, instance.mac) = cloud.register_instance(path=instance.path, name=args.name)
            instance.metadata = CIMetadata(instance.instance_id, args.name)
            instance.userdata = CIUserData(phone_home_url=f'http://{cloud.host_ip4}:{cloud.ph_port}/$INSTANCE_ID',
                                           pubkey=cloud.public_key)
            instance.userdata.admin_password = cloud.admin_password
            instance.vendordata = CIVendorData()
            instance.network_config = CINetworkConfig(mac=instance.mac,
                                                      ipv4=args.ip,
                                                      nm4=cloud.host_nm4,
                                                      gw4=cloud.host_gw4,
                                                      ns4=cloud.host_ns4)
            instance.create()

            status.update('Waiting for the instance to phone home')
            httpd = PhoneHomeServer(server_address=(cloud.host_ip4, cloud.ph_port),
                                    callback=instance.configure,
                                    RequestHandlerClass=PhoneHomeHandler)
            httpd.timeout = 120
            httpd.handle_request()
        return 0

    @staticmethod
    def remove(args: argparse.Namespace, config: configparser.ConfigParser) -> int:   # pylint: disable=unused-argument
        with console.status(f'[magenta] Removing instance {args.name}') as status:
            cloud = Cloud(path=args.path)
            cloud.load()

            instance_path = cloud.instances_path.joinpath(args.name)
            if not instance_path.exists():
                console.log(f'Instance at {instance_path} does not exist')
                return 0
            status.update(f'Removing instance at {instance_path}')
            shutil.rmtree(instance_path)
            console.log(f'Removed instance at {instance_path}')
        return 0
