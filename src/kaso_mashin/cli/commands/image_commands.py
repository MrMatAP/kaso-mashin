import argparse
import uuid
import time

import rich.table
import rich.box
import rich.tree
import rich.columns
import rich.progress

from kaso_mashin import console
from kaso_mashin.cli.commands import AbstractCommands
from kaso_mashin.common.base_types import BinaryScale, BinarySizedValue
from kaso_mashin.common.entities import (
    TaskGetSchema, TaskState,
    ImageListSchema, ImageGetSchema, ImageCreateSchema, ImageModifySchema)
from kaso_mashin.common.config import Predefined_Images


class ImageCommands(AbstractCommands):
    """
    Implementation of the image command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        image_subparser = parser.add_subparsers()
        image_list_parser = image_subparser.add_parser(name='list', help='List images')
        image_list_parser.set_defaults(cmd=self.list)
        image_get_parser = image_subparser.add_parser(name='get', help='Get a image')
        image_get_parser.add_argument('--uid',
                                      dest='uid',
                                      type=uuid.UUID,
                                      help='The image uid')
        image_get_parser.set_defaults(cmd=self.get)
        image_create_parser = image_subparser.add_parser(name='create', help='Create an image')
        image_create_parser.add_argument('-n', '--name',
                                         dest='name',
                                         type=str,
                                         required=True,
                                         help='The image name')
        image_create_predefined_or_url = image_create_parser.add_mutually_exclusive_group(required=True)
        image_create_predefined_or_url.add_argument('--url',
                                                    dest='url',
                                                    type=str,
                                                    help='Provide the URL to the cloud image')
        image_create_predefined_or_url.add_argument('--predefined',
                                                    dest='predefined',
                                                    type=str,
                                                    choices=Predefined_Images.keys(),
                                                    help='Pick a predefined image')
        image_create_parser.add_argument('--min-vcpu',
                                         dest='min_vcpu',
                                         type=int,
                                         default=0,
                                         help='An optional number of minimum vCPUs for this image')
        image_create_parser.add_argument('--min-ram',
                                         dest='min_ram',
                                         type=int,
                                         default=0,
                                         help='An optional number of minimum RAM for this image')
        image_create_parser.add_argument('--min-ram-scale',
                                         dest='min_ram_scale',
                                         type=BinaryScale,
                                         default=BinaryScale.G,
                                         help='Scale of the minimum RAM specification')
        image_create_parser.add_argument('--min-disk',
                                         dest='min_disk',
                                         type=int,
                                         default=0,
                                         help='An optional number of minimum disk space for this image')
        image_create_parser.add_argument('--min-disk-scale',
                                         dest='min_disk_scale',
                                         type=BinaryScale,
                                         default=BinaryScale.G,
                                         help='Scale of the minimum disk space specification')
        image_create_parser.set_defaults(cmd=self.create)
        image_modify_parser = image_subparser.add_parser(name='modify', help='Modify an image')
        image_modify_parser.add_argument('--uid',
                                         dest='uid',
                                         type=int,
                                         required=True,
                                         help='The image uid')
        image_modify_parser.add_argument('--min-cpu',
                                         dest='min_cpu',
                                         type=int,
                                         default=None,
                                         help='An optional number of minimum vCPUs for this image')
        image_modify_parser.add_argument('--min-ram',
                                         dest='min_ram',
                                         type=int,
                                         default=None,
                                         help='An optional number of minimum RAM (in MB) for this image')
        image_modify_parser.add_argument('--min-ram-scale',
                                         dest='min_ram_scale',
                                         type=BinaryScale,
                                         default=BinaryScale.G,
                                         help='Scale of the minimum RAM specification')
        image_modify_parser.add_argument('--min-disk',
                                         dest='min_disk',
                                         type=int,
                                         default=0,
                                         help='An optional number of minimum disk space for this image')
        image_modify_parser.add_argument('--min-disk-scale',
                                         dest='min_disk_scale',
                                         type=BinaryScale,
                                         default=BinaryScale.G,
                                         help='Scale of the minimum disk space specification')
        image_modify_parser.set_defaults(cmd=self.modify)
        image_remove_parser = image_subparser.add_parser(name='remove', help='Remove an image')
        image_remove_parser.add_argument('--uid',
                                         dest='uid',
                                         type=int,
                                         required=True,
                                         help='The image uid')
        image_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:
        del args
        resp = self.api_client(uri='/api/images/',
                               expected_status=[200])
        if not resp:
            return 1
        images = [ImageListSchema.model_validate(img) for img in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]ID')
        table.add_column('[blue]Name')
        for image in images:
            table.add_row(str(image.uid), image.name)
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/images/{args.uid}',
                               expected_status=[200],
                               fallback_msg='Image not found')
        if not resp:
            return 1
        image = ImageGetSchema.model_validate_json(resp.content)
        self._print_image(image)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        create_schema = ImageCreateSchema(name=args.name,
                                          url=args.url or Predefined_Images.get(args.predefined),
                                          min_vcpu=args.min_vcpu,
                                          min_ram=BinarySizedValue(value=args.min_ram, scale=args.min_ram_scale),
                                          min_disk=BinarySizedValue(value=args.min_disk, scale=args.min_disk_scale))
        if args.url:
            create_schema.url = args.url
        resp = self.api_client(uri='/api/images/',
                               method='POST',
                               body=create_schema.model_dump(),
                               expected_status=[201],
                               fallback_msg='Failed to download image')
        if not resp:
            return 1
        task = TaskGetSchema.model_validate(resp.json())
        with rich.progress.Progress() as progress:
            download_task = progress.add_task(f'[green]Download image {args.name}...', total=100, visible=True)
            while not task.state == TaskState.DONE:
                resp = self.api_client(uri=f'/api/tasks/{task.uid}',
                                       expected_status=[200],
                                       fallback_msg=f'Failed to fetch status for task {task.uid}')
                if not resp:
                    return 1
                task = TaskGetSchema.model_validate(resp.json())
                if task.state == TaskState.FAILED:
                    progress.update(download_task, completed=100, refresh=True,
                                    description=f'Failed: {task.msg}',
                                    visible=False)
                    console.print(f'[red]ERROR[/red]: {task.msg}')
                    return 1
                else:
                    progress.update(download_task, completed=task.percent_complete, refresh=True)
                time.sleep(2)
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = ImageModifySchema(min_vcpu=args.min_cpu or -1,
                                   min_ram=BinarySizedValue(value=args.min_ram, scale=args.min_ram_scale),
                                   min_disk=BinarySizedValue(value=args.min_disk, scale=args.min_disk_scale))
        resp = self.api_client(uri=f'/api/images/{args.uid}',
                               method='PUT',
                               body=schema.model_dump(),
                               expected_status=[200],
                               fallback_msg='Failed to modify image')
        if not resp:
            return 1
        image = ImageGetSchema.model_validate_json(resp.content)
        self._print_image(image)
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(f'/api/images/{args.uid}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove image')
        if not resp:
            return 1
        if resp.status_code == 204:
            console.print(f'Removed image with id {args.uid}')
        elif resp.status_code == 410:
            console.print(f'Image with id {args.uid} does not exist')
        return 0 if resp else 1

    @staticmethod
    def _print_image(image: ImageGetSchema):
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]UID', str(image.uid))
        table.add_row('[blue]Name', image.name)
        table.add_row('[blue]Path', str(image.path))
        table.add_row('[blue]Min VCPU', str(image.min_vcpu))
        table.add_row('[blue]Min RAM', f'{image.min_ram.value} {image.min_ram.scale}')
        table.add_row('[blue]Min Disk', f'{image.min_disk.value} {image.min_disk.scale}')
        console.print(table)
