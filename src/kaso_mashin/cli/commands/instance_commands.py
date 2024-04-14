import argparse
import uuid
import time

import rich.table
import rich.box
import rich.columns
import rich.progress

from kaso_mashin import console
from kaso_mashin.cli.commands import AbstractCommands
from kaso_mashin.common.base_types import BinaryScale, BinarySizedValue
from kaso_mashin.common.entities import (
    TaskGetSchema, TaskState, InstanceState,
    InstanceListSchema, InstanceGetSchema, InstanceCreateSchema, InstanceModifySchema)


class InstanceCommands(AbstractCommands):
    """
    Implementation of instance command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        instance_subparser = parser.add_subparsers()
        instance_list_parser = instance_subparser.add_parser(name='list', help='List instances')
        instance_list_parser.set_defaults(cmd=self.list)
        instance_get_parser = instance_subparser.add_parser(name='get', help='Get an instance')
        instance_get_parser.add_argument('--uid',
                                         dest='uid',
                                         type=uuid.UUID,
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
                                            default=2,
                                            help='Amount of RAM in MB to assign to this instance')
        instance_create_parser.add_argument('--ram-scale',
                                            dest='ram_scale',
                                            type=BinaryScale,
                                            required=False,
                                            default=BinaryScale.G,
                                            help='Scale for the amount of RAM')
        instance_create_parser.add_argument('--os-disk',
                                            dest='os_disk',
                                            type=int,
                                            required=False,
                                            default=10,
                                            help='Amount of OS disk space')
        instance_create_parser.add_argument('--os-disk-scale',
                                            dest='os_disk_scale',
                                            type=BinaryScale,
                                            required=False,
                                            default=BinaryScale.G,
                                            help='Scale for the amount of OS disk space')
        instance_create_parser.add_argument('--image-uid',
                                            dest='image_uid',
                                            type=str,
                                            required=True,
                                            help='UID of the image for the OS disk')
        instance_create_parser.add_argument('--network-uid',
                                            dest='network_uid',
                                            type=str,
                                            required=True,
                                            help='The network uid on which this instance should be attached')
        instance_create_parser.add_argument('--bootstrap-uid',
                                            dest='bootstrap_uid',
                                            type=str,
                                            required=True,
                                            help='The bootstrap uid using which this instance should be created')
        instance_create_parser.set_defaults(cmd=self.create)
        instance_modify_parser = instance_subparser.add_parser(name='modify', help='Modify an instance')
        instance_modify_parser.add_argument('--uid',
                                            dest='uid',
                                            type=uuid.UUID,
                                            help='The instance uid')
        instance_modify_parser.set_defaults(cmd=self.modify)
        instance_remove_parser = instance_subparser.add_parser(name='remove', help='Remove an instance')
        instance_remove_parser.add_argument('--uid',
                                            dest='uid',
                                            type=uuid.UUID,
                                            required=True,
                                            help='The instance uid')
        instance_remove_parser.set_defaults(cmd=self.remove)
        instance_start_parser = instance_subparser.add_parser(name='start', help='Start an instance')
        instance_start_parser.add_argument('--uid',
                                           dest='uid',
                                           type=uuid.UUID,
                                           required=True,
                                           help='The instance uid')
        instance_start_parser.set_defaults(cmd=self.start)
        instance_stop_parser = instance_subparser.add_parser(name='stop', help='Stop an instance')
        instance_stop_parser.add_argument('--id',
                                          dest='uid',
                                          type=uuid.UUID,
                                          required=True,
                                          help='The instance uid')
        instance_stop_parser.set_defaults(cmd=self.stop)

    def list(self, args: argparse.Namespace) -> int:
        del args
        resp = self.api_client(uri='/api/instances/', expected_status=[200])
        if not resp:
            return 1
        instances = [InstanceListSchema.model_validate(instance) for instance in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]ID')
        table.add_column('[blue]Name')
        for instance in instances:
            table.add_row(str(instance.uid), instance.name)
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/instances/{args.uid}',
                               expected_status=[200],
                               fallback_msg=f'Instance with id {args.uid} could not be found')
        if not resp:
            return 1
        instance = InstanceGetSchema.model_validate_json(resp.content)
        console.print(instance)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        schema = InstanceCreateSchema(name=args.name,
                                             vcpu=args.vcpu,
                                             ram=BinarySizedValue(value=args.ram, scale=args.ram_scale),
                                             os_disk_size=BinarySizedValue(value=args.os_disk, scale=args.os_disk_scale),
                                             image_uid=args.image_uid,
                                             network_uid=args.network_uid,
                                             bootstrap_uid=args.bootstrap_uid)
        resp = self.api_client(uri='/api/instances/',
                               method='POST',
                               schema=schema,
                               expected_status=[201],
                               fallback_msg='Failed to create instance')
        if not resp:
            return 1
        task = TaskGetSchema.model_validate(resp.json())
        with rich.progress.Progress() as progress:
            create_task = progress.add_task(f'[green]Creating instance {args.name}...', total=100)
            while not task.state == TaskState.DONE:
                resp = self.api_client(uri=f'/api/tasks/{task.uid}',
                                       expected_status=[200],
                                       fallback_msg=f'Failed to fetch status for task {task.uid}')
                if not resp:
                    return 1
                task = TaskGetSchema.model_validate(resp.json())
                if task.state == TaskState.FAILED:
                    progress.update(create_task, completed=100, refresh=True,
                                    description=f'Failed: {task.msg}')
                    return 1
                else:
                    progress.update(create_task, completed=task.percent_complete, refresh=True)
                time.sleep(2)
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        del args
        console.print('[yellow]Not yet implemented')
        return 1

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/instances/{args.uid}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove instance')
        if not resp:
            return 1
        if resp.status_code == 204:
            console.print(f'Removed instance with id {args.uid}')
        elif resp.status_code == 410:
            console.print(f'Identity with id {args.uid} does not exist')
        return 0 if resp else 1

    def start(self, args: argparse.Namespace) -> int:
        schema = InstanceModifySchema(state=InstanceState.STARTED)
        resp = self.api_client(uri=f'/api/instances/{args.uid}',
                               method='PUT',
                               schema=schema,
                               expected_status=[200],
                               fallback_msg='Failed to start instance')
        return 0 if resp else 1

    def stop(self, args: argparse.Namespace) -> int:
        schema = InstanceModifySchema(state=InstanceState.STOPPED)
        resp = self.api_client(uri=f'/api/instances/{args.uid}/state',
                               method='PUT',
                               schema=schema,
                               expected_status=[200],
                               fallback_msg='Failed to start instance')
        return 0 if resp else 1
