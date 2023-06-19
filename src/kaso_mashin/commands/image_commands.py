import argparse

import requests
import rich.progress

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import ImageURLs, ImageModel


class ImageCommands(AbstractCommands):
    """
    Implementation of the image command group
    """

    def register_commands(self, parser: argparse.ArgumentParser):
        image_subparser = parser.add_subparsers()
        image_list_parser = image_subparser.add_parser(name='list', help='List images')
        image_list_parser.set_defaults(cmd=self.list)
        image_get_parser = image_subparser.add_parser(name='get', help='Get a image')
        image_get_parser.add_argument('--id',
                                      dest='id',
                                      type=int,
                                      required=True,
                                      help='The image id')
        image_get_parser.set_defaults(cmd=self.get)
        image_download_parser = image_subparser.add_parser(name='download', help='Download an image')
        image_download_parser.add_argument('-n', '--name',
                                           dest='name',
                                           type=str,
                                           choices=ImageURLs.keys(),
                                           required=True,
                                           help='The image to download')
        image_download_parser.set_defaults(cmd=self.download)
        image_remove_parser = image_subparser.add_parser(name='remove', help='Remove an image')
        image_remove_parser.add_argument('--id',
                                      dest='id',
                                      type=int,
                                      required=True,
                                      help='The image id')
        image_remove_parser.set_defaults(cmd=self.remove)

    def list(self, args: argparse.Namespace) -> int:        # pylint: disable=unused-argument
        images = self.image_controller.list()
        for image in images:
            console.print(f'- Id:   {image.image_id}')
            console.print(f'  Name: {image.name}')
            console.print(f'  Path: {image.path}')
        return 0

    def get(self, args: argparse.Namespace) -> int:
        image = self.image_controller.get(args.id)
        if not image:
            console.print(f'ERROR: Image with id {args.id} not found')
            return 1
        console.print(f'- Id:   {image.image_id}')
        console.print(f'  Name: {image.name}')
        console.print(f'  Path: {image.path}')
        return 0

    def download(self, args: argparse.Namespace) -> int:
        with console.status(f'[magenta] Downloading image {args.name}') as status:
            image_url = ImageURLs.get(args.name)
            image_path = self.config.path.joinpath(f'images/{args.name}.qcow2')
            if image_path.exists():
                status.update(f'ERROR: Image at path {image_path} already exists. Please remove it first.')
                return 1

            resp = requests.head(image_url, allow_redirects=True, timeout=60)
            size = int(resp.headers.get('content-length'))
            current = 0

            with rich.progress.Progress() as progress:
                download_task = progress.add_task(f'[green]Download image {args.name}...', total=100, visible=True)
                with requests.get(image_url,
                                  allow_redirects=True,
                                  stream=True,
                                  timeout=60) as resp, \
                        open(image_path, 'wb') as i:
                    for chunk in resp.iter_content(chunk_size=8192):
                        i.write(chunk)
                        current += 8192
                        progress.update(download_task, completed=current / size * 100, refresh=True)

            image = ImageModel(name=args.name, path=str(image_path))
            image = self.image_controller.create(image)
            status.update(f'Downloaded image {image.image_id}: {image.name} to {image.path}')
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        self.image_controller.remove(args.id)
        return 0
