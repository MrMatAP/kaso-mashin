import argparse
import httpx
import fastapi
import time

import rich.table
import rich.box
import rich.tree
import rich.columns
import rich.progress

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import ImageURLs, TaskSchema, TaskState, ImageSchema, ImageCreateSchema


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
        image_download_parser = image_subparser.add_parser(name='download', help='Download an image')
        image_download_parser.add_argument('-n', '--name',
                                           dest='name',
                                           type=str,
                                           required=True,
                                           help='The image name')
        image_download_parser.add_argument('--common',
                                           dest='common',
                                           type=str,
                                           choices=ImageURLs.keys(),
                                           required=True,
                                           help='Common images')
        image_download_parser.set_defaults(cmd=self.download)
        image_remove_parser = image_subparser.add_parser(name='remove', help='Remove an image')
        image_remove_parser.add_argument('--id',
                                         dest='image_id',
                                         type=int,
                                         required=True,
                                         help='The image id')
        image_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
        resp = httpx.get(f'{self.server_url}/api/images/', timeout=60)
        if resp.status_code != 200:
            console.print('ERROR: Failed to make API call')
            return 1
        images = [ImageSchema.model_validate(img) for img in resp.json()]
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('ID')
        table.add_column('Name')
        table.add_column('Path')
        for image in images:
            table.add_row(str(image.image_id), image.name, str(image.path))
        console.print(table)
        return 0

    def get(self, args: argparse.Namespace) -> int:
        resp = httpx.get(f'{self.server_url}/api/images/{args.image_id}', timeout=60)
        if resp.status_code != 200:
            console.print(f'ERROR: Image with id {args.image_id} not found')
            return 1
        image = ImageSchema.model_validate_json(resp.content)
        table = rich.table.Table(box=rich.box.ROUNDED)
        table.add_column('Field')
        table.add_column('Value')
        table.add_row('[blue]Id', str(image.image_id))
        table.add_row('[blue]Name', image.name)
        table.add_row('[blue]Path', str(image.path))
        console.print(table)
        return 0

    def download(self, args: argparse.Namespace) -> int:
        create_schema = ImageCreateSchema(name=args.name, url=ImageURLs.get(args.common)).model_dump()
        resp = httpx.put(f'{self.server_url}/api/images/', json=create_schema)
        if resp.status_code != 200:
            console.print('Failed to download image')
            return 1
        task = TaskSchema.model_validate(resp.json())
        with rich.progress.Progress() as progress:
            download_task = progress.add_task(f'[green]Download image {args.name}...', total=100, visible=True)
            while not task.state == TaskState.DONE:
                resp = httpx.get(f'{self.server_url}/api/tasks/{task.task_id}')
                if resp.status_code != 200:
                    console.print(f'Failed to fetch status for task {task.task_id}')
                    return 1
                task = TaskSchema.model_validate(resp.json())
                progress.update(download_task, completed=task.percent_complete, refresh=True)
                time.sleep(2)
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        resp = httpx.delete(f'{self.server_url}/api/images/{args.image_id}', timeout=60)
        if resp.status_code in [fastapi.status.HTTP_410_GONE, fastapi.status.HTTP_204_NO_CONTENT]:
            console.print(f'Successfully removed image with id {args.image_id}')
            return 0
        console.print(f'ERROR: Failed to remove image with id {args.image_id}')
        return 1
