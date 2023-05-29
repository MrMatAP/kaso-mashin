import argparse
import configparser

import requests
import rich.progress

from kaso_mashin import console
from kaso_mashin.model import Cloud


class ImageCommands:
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

    @staticmethod
    def download(args: argparse.Namespace, config: configparser.ConfigParser) -> int:   # pylint: disable=unused-argument
        cloud = Cloud(path=args.path)
        cloud.load()

        if args.name not in ImageCommands.IMAGE_URLS:
            console.log(f'ERROR: Image with name {args.name} is not known. Please download it manually.')
            return 1
        image_url = ImageCommands.IMAGE_URLS.get(args.name)
        image_path = cloud.images_path.joinpath(f'{args.name}.qcow2')
        if image_path.exists():
            console.log(f'Image at path {image_path} already exists. Please remove it first.')
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
