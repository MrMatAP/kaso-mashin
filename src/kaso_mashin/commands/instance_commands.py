import argparse
import time

import rich.table
import rich.box
import rich.columns
import rich.progress

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import (
    TaskSchema, TaskState,
    InstanceSchema, InstanceCreateSchema,
    DisplayKind, BootstrapKind)


class InstanceCommands(AbstractCommands):
    """
    Implementation of instance command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        instance_subparser = parser.add_subparsers()
        instance_list_parser = instance_subparser.add_parser(name='list', help='List instances')
        instance_list_parser.set_defaults(cmd=self.list)
        instance_get_parser = instance_subparser.add_parser(name='get', help='Get an instance')
        instance_get_id_or_name = instance_get_parser.add_mutually_exclusive_group(required=True)
        instance_get_id_or_name.add_argument('--id',
                                             dest='instance_id',
                                             type=int,
                                             help='The instance id')
        instance_get_id_or_name.add_argument('--name',
                                             dest='name',
                                             type=str,
                                             help='The instance name')
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
        instance_create_parser.add_argument('--display',
                                            dest='display',
                                            type=str,
                                            required=False,
                                            default=DisplayKind.VNC,
                                            choices=[k.value for k in DisplayKind],
                                            help='How this VM should show its display')
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
                                            required=False,
                                            default=[],
                                            action='append',
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
        instance_modify_parser = instance_subparser.add_parser(name='modify', help='Modify an instance')
        instance_modify_parser.add_argument('--id',
                                            dest='instance_id',
                                            type=int,
                                            help='The instance id')
        instance_modify_parser.set_defaults(cmd=self.modify)
        instance_remove_parser = instance_subparser.add_parser(name='remove', help='Remove an instance')
        instance_remove_parser.add_argument('--id',
                                            dest='instance_id',
                                            type=int,
                                            required=True,
                                            help='The instance id')
        instance_remove_parser.set_defaults(cmd=self.remove)
        instance_start_parser = instance_subparser.add_parser(name='start', help='Start an instance')
        instance_start_parser.add_argument('--id',
                                           dest='instance_id',
                                           type=int,
                                           required=True,
                                           help='The instance id')
        instance_start_parser.set_defaults(cmd=self.start)
        instance_stop_parser = instance_subparser.add_parser(name='stop', help='Stop an instance')
        instance_stop_parser.add_argument('--id',
                                          dest='instance_id',
                                          type=int,
                                          required=True,
                                          help='The instance id')
        instance_stop_parser.set_defaults(cmd=self.stop)

    def list(self, args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
        resp = self.api_client(uri='/api/instances/', expected_status=[200])
        if not resp:
            return 1
        instances = [InstanceSchema.model_validate(instance) for instance in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]ID')
        table.add_column('[blue]Name')
        table.add_column('[blue]Path')
        table.add_column('[blue]Image ID')
        table.add_column('[blue]Network ID')
        for instance in instances:
            table.add_row(str(instance.instance_id),
                          instance.name,
                          str(instance.path),
                          str(instance.image_id),
                          str(instance.network_id))
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/instances/{args.instance_id}',
                               expected_status=[200],
                               fallback_msg=f'Instance with id {args.instance_id} could not be found')
        if not resp:
            return 1
        instance = InstanceSchema.model_validate_json(resp.content)
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]Id', str(instance.instance_id))
        table.add_row('[blue]Name', instance.name)
        table.add_row('[blue]Path', str(instance.path))
        table.add_row('[blue]MAC', instance.mac)
        table.add_row('[blue]vCPUs', str(instance.vcpu))
        table.add_row('[blue]RAM', str(instance.ram))
        table.add_row('[blue]Display', instance.display)
        table.add_row('[blue]Bootstrapper', instance.bootstrapper)
        table.add_row('[blue]Image ID', str(instance.image_id))
        table.add_row('[blue]Network ID', str(instance.network_id))
        table.add_row('[blue]OS Disk Path', str(instance.os_disk_path))
        table.add_row('[blue]OS Disk Size', instance.os_disk_size)
        table.add_row('[blue]CI Base Path', str(instance.ci_base_path))
        table.add_row('[blue]CI Disk path', str(instance.ci_disk_path))
        table.add_row('[blue]VM Script Path', str(instance.vm_script_path))
        table.add_row('[blue]VNC Socket Path', str(instance.vnc_path))
        table.add_row('[blue]QMP Socket Path', str(instance.qmp_path))
        table.add_row('[blue]Console Socket Path', str(instance.console_path))
        console.print(table)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        create_schema = InstanceCreateSchema(name=args.name,
                                             vcpu=args.vcpu,
                                             ram=args.ram,
                                             display=args.display,
                                             network_id=args.network_id,
                                             image_id=args.image_id,
                                             identities=args.identity_id,
                                             bootstrapper=args.bootstrapper,
                                             os_disk_size=args.os_disk_size or self.config.default_os_disk_size)
        resp = self.api_client(uri='/api/instances/',
                               method='POST',
                               body=create_schema.model_dump(),
                               expected_status=[201],
                               fallback_msg='Failed to create instance')
        if not resp:
            return 1
        task = TaskSchema.model_validate(resp.json())
        with rich.progress.Progress() as progress:
            create_task = progress.add_task(f'[green]Creating instance {args.name}...', total=100)
            while not task.state == TaskState.DONE:
                resp = self.api_client(uri=f'/api/tasks/{task.task_id}',
                                       expected_status=[200],
                                       fallback_msg=f'Failed to fetch status for task {task.task_id}')
                if not resp:
                    return 1
                task = TaskSchema.model_validate(resp.json())
                if task.state == TaskState.FAILED:
                    progress.update(create_task, completed=100, refresh=True,
                                    description=f'Failed: {task.msg}')
                    return 1
                else:
                    progress.update(create_task, completed=task.percent_complete, refresh=True)
                time.sleep(2)
        return 0

    def modify(self, args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
        console.print('[yellow]Not yet implemented')
        return 1

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/instances/{args.instance_id}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove instance')
        return 0 if resp else 1

    def start(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/instances/{args.instance_id}/state',
                               method='POST',
                               expected_status=[200],
                               fallback_msg='Failed to start instance')
        return 0 if resp else 1

    def stop(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/instances/{args.instance_id}/state',
                               method='DELETE',
                               expected_status=[200],
                               fallback_msg='Failed to start instance')
        return 0 if resp else 1
