import shutil
import pathlib

from kaso_mashin import KasoMashinException
from kaso_mashin.executor import execute
from kaso_mashin.controllers import AbstractController


class DiskController(AbstractController):
    """
    A disk controller
    """

    def create(self, path: pathlib.Path, backing_disk_path: pathlib.Path):
        if path.exists():
            raise KasoMashinException(status=400, msg=f'Disk at {path} already exists')
        if not backing_disk_path.exists():
            raise KasoMashinException(status=400, msg=f'Backing disk at {backing_disk_path} does not exist')
        execute('qemu-img', ['create', '-f', 'qcow2', '-b', backing_disk_path, '-F', 'qcow2', path])

    def modify(self, path: pathlib.Path, size: str):
        if not path.exists():
            raise KasoMashinException(status=400, msg=f'Disk at {path} does not exist')
        execute('qemu-img', ['resize', path, size])

    def remove(self, path: pathlib.Path):
        if not path.exists():
            raise KasoMashinException(status=400, msg=f'Disk at {path} does not exist')
        shutil.rmtree(path)
