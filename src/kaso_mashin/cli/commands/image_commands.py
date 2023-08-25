import argparse
import time

import rich.table
import rich.box
import rich.tree
import rich.columns
import rich.progress

from kaso_mashin import console
from kaso_mashin.cli.commands import AbstractCommands
from kaso_mashin.common.model import (
    Predefined_Images,
    TaskSchema, TaskState,
    ImageSchema, ImageCreateSchema, ImageModifySchema )


class ImageCommands(AbstractCommands):
    """
    Implementation of the image command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        image_subparser = parser.add_subparsers()
        image_list_parser = image_subparser.add_parser(name='list', help='List images')
        image_list_parser.set_defaults(cmd=self.list)
        image_get_parser = image_subparser.add_parser(name='get', help='Get a image')
        image_get_id_or_name = image_get_parser.add_mutually_exclusive_group(required=True)
        image_get_id_or_name.add_argument('--id',
                                          dest='image_id',
                                          type=int,
                                          help='The image id')
        image_get_id_or_name.add_argument('--name',
                                          dest='name',
                                          type=str,
                                          help='The image name')
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
        image_create_parser.add_argument('--min-cpu',
                                         dest='min_cpu',
                                         type=int,
                                         default=0,
                                         help='An optional number of minimum vCPUs for this image')
        image_create_parser.add_argument('--min-ram',
                                         dest='min_ram',
                                         type=int,
                                         default=0,
                                         help='An optional number of minimum RAM (in MB) for this image')
        image_create_parser.add_argument('--min-space',
                                         dest='min_space',
                                         type=int,
                                         default=0,
                                         help='An optional number of minimum disk space (in MB) for this image')
        image_create_parser.set_defaults(cmd=self.create)
        image_modify_parser = image_subparser.add_parser(name='modify', help='Modify an image')
        image_modify_parser.add_argument('--id',
                                         dest='image_id',
                                         type=int,
                                         required=True,
                                         help='The image id')
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
        image_modify_parser.add_argument('--min-space',
                                         dest='min_space',
                                         type=int,
                                         default=None,
                                         help='An optional number of minimum disk space (in MB) for this image')
        image_modify_parser.set_defaults(cmd=self.modify)
        image_remove_parser = image_subparser.add_parser(name='remove', help='Remove an image')
        image_remove_parser.add_argument('--id',
                                         dest='image_id',
                                         type=int,
                                         required=True,
                                         help='The image id')
        image_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
        resp = self.api_client(uri='/api/images/',
                               expected_status=[200])
        if not resp:
            return 1
        images = [ImageSchema.model_validate(img) for img in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('[blue]ID')
        table.add_column('[blue]Name')
        table.add_column('[blue]Path')
        for image in images:
            table.add_row(str(image.image_id), image.name, str(image.path))
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = self.api_client(uri=f'/api/images/{args.image_id}',
                               expected_status=[200],
                               fallback_msg='Image not found')
        if not resp:
            return 1
        image = ImageSchema.model_validate_json(resp.content)
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]Id', str(image.image_id))
        table.add_row('[blue]Name', image.name)
        table.add_row('[blue]Path', str(image.path))
        table.add_row('[blue]Minimum vCPUs', str(image.min_cpu))
        table.add_row('[blue]Minimum RAM (MB)', str(image.min_ram))
        table.add_row('[blue]Minimum Disk Space (MB)', str(image.min_space))
        console.print(table)
        return 0

    def create(self, args: argparse.Namespace) -> int:
        create_schema = ImageCreateSchema(name=args.name,
                                          url=args.url or Predefined_Images.get(args.predefined),
                                          min_cpu=args.min_cpu,
                                          min_ram=args.min_ram,
                                          min_space=args.min_space)
        if args.url:
            create_schema.url = args.url
        resp = self.api_client(uri='/api/images/',
                               method='POST',
                               body=create_schema.model_dump(),
                               expected_status=[201],
                               fallback_msg='Failed to download image')
        if not resp:
            return 1
        task = TaskSchema.model_validate(resp.json())
        with rich.progress.Progress() as progress:
            download_task = progress.add_task(f'[green]Download image {args.name}...', total=100, visible=True)
            while not task.state == TaskState.DONE:
                resp = self.api_client(uri=f'/api/tasks/{task.task_id}',
                                       expected_status=[200],
                                       fallback_msg=f'Failed to fetch status for task {task.task_id}')
                if not resp:
                    return 1
                task = TaskSchema.model_validate(resp.json())
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
        schema = ImageModifySchema(min_cpu=args.min_cpu or -1,
                                   min_ram=args.min_ram or -1,
                                   min_space=args.min_space or -1)
        resp = self.api_client(uri=f'/api/images/{args.image_id}',
                               method='PUT',
                               body=schema.model_dump(),
                               expected_status=[200],
                               fallback_msg='Failed to modify image')
        if not resp:
            return 1
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        resp = self.api_client(f'/api/images/{args.image_id}',
                               method='DELETE',
                               expected_status=[204, 410],
                               fallback_msg='Failed to remove image')
        if not resp:
            return 1
        return 1
