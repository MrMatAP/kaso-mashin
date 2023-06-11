import argparse

import requests
import rich.progress

from kaso_mashin import console
from kaso_mashin.commands import AbstractCommands
from kaso_mashin.model import ImageModel
from kaso_mashin.controllers import ImageController


class ImageCommands(AbstractCommands):
    """
    Implementation of image commands
    """

    IMAGE_URLS = {
        'ubuntu-bionic': 'https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img',
        'ubuntu-focal': 'https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-arm64.img',
        'ubuntu-jammy': 'https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img',
        'ubuntu-kinetic': 'https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-arm64.img',
        'ubuntu-lunar': 'https://cloud-images.ubuntu.com/lunar/current/lunar-server-cloudimg-arm64.img',
        'ubuntu-mantic': 'https://cloud-images.ubuntu.com/mantic/current/mantic-server-cloudimg-arm64.img',
        'freebsd-14': 'https://download.freebsd.org/ftp/snapshots/VM-IMAGES/14.0-CURRENT/amd64/Latest/'
                      'FreeBSD-14.0-CURRENT-amd64.qcow2.xz'
    }

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
                                           choices=ImageCommands.IMAGE_URLS,
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

    def list(self, args: argparse.Namespace) -> int:
        image_controller = ImageController(config=self.config, db=self.db)
        images = image_controller.list()
        for image in images:
            console.print(f'- Id:   {image.image_id}')
            console.print(f'  Name: {image.name}')
            console.print(f'  Path: {image.path}')
        return 0

    def get(self, args: argparse.Namespace) -> int:
        image_controller = ImageController(config=self.config, db=self.db)
        image = image_controller.get(args.id)
        if not image:
            console.print(f'ERROR: Image with id {args.id} not found')
            return 1
        console.print(f'- Id:   {image.image_id}')
        console.print(f'  Name: {image.name}')
        console.print(f'  Path: {image.path}')
        return 0

    def download(self, args: argparse.Namespace) -> int:
        image_controller = ImageController(config=self.config, db=self.db)
        with console.status(f'[magenta] Downloading image {args.name}') as status:
            if args.name not in ImageCommands.IMAGE_URLS:
                status.update(f'ERROR: Image with name {args.name} is not known. Please download it manually')
                return 1
            image_url = ImageCommands.IMAGE_URLS.get(args.name)
            image_path = self.config.path.joinpath(f'images/{args.name}.qcow2')
            if image_path.exists():
                status.update(f'ERROR: Image at path {image_path} already exists. Please remove it first.')
                return 1

            resp = requests.head(image_url, allow_redirects=True, timeout=60)
            size = int(resp.headers.get('content-length'))
            current = 0

            with rich.progress.Progress() as progress:
                download_task = progress.add_task(f'[green]Download image {args.name}...', total=100, visible=True)
                with requests.get(ImageCommands.IMAGE_URLS.get(args.name),
                                  allow_redirects=True,
                                  stream=True,
                                  timeout=60) as resp, \
                        open(image_path, 'wb') as i:
                    for chunk in resp.iter_content(chunk_size=8192):
                        i.write(chunk)
                        current += 8192
                        progress.update(download_task, completed=current / size * 100, refresh=True)

            image = ImageModel(name=args.name, path=str(image_path))
            image = image_controller.create(image)
            status.update(f'Downloaded image {image.image_id}: {image.name} to {image.path}')
        return 0

    def remove(self, args: argparse.Namespace) -> int:
        image_controller = ImageController(config=self.config, db=self.db)
        image_controller.remove(args.id)
        return 0
