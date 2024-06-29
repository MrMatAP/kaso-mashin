import argparse
import uuid
import time

import rich.table
import rich.box
import rich.tree
import rich.columns
import rich.progress

from kaso_mashin import console
from kaso_mashin.cli.commands import BaseCommands
from kaso_mashin.common.base_types import (
    BinaryScale,
    BinarySizedValue,
    UniqueIdentifier,
)
from kaso_mashin.common.entities import (
    TaskGetSchema,
    TaskState,
    ImageListSchema,
    ImageGetSchema,
    ImageCreateSchema,
    ImageModifySchema,
)
from kaso_mashin.common.config import Predefined_Images, Config, PredefinedImageSchema


class ImageCommands(BaseCommands[ImageListSchema, ImageGetSchema]):
    """
    Implementation of the image command group
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self._prefix = "/api/images"
        self._list_schema_type = ImageListSchema
        self._get_schema_type = ImageGetSchema
        self._predefined_images = [pi.name for pi in Predefined_Images]

    def register_commands(self, parser: argparse.ArgumentParser):
        image_subparser = parser.add_subparsers()
        image_list_parser = image_subparser.add_parser(name="list", help="List images")
        image_list_parser.set_defaults(cmd=self.list)
        image_get_parser = image_subparser.add_parser(name="get", help="Get a image")
        image_get_parser.add_argument(
            "--uid", dest="uid", type=UniqueIdentifier, help="The image uid"
        )
        image_get_parser.set_defaults(cmd=self.get)
        image_create_parser = image_subparser.add_parser(name="create", help="Create an image")
        image_create_parser.add_argument(
            "-n", "--name", dest="name", type=str, required=True, help="The image name"
        )
        image_create_predefined_or_url = image_create_parser.add_mutually_exclusive_group(
            required=True
        )
        image_create_predefined_or_url.add_argument(
            "--url", dest="url", type=str, help="Provide the URL to the cloud image"
        )
        image_create_predefined_or_url.add_argument(
            "--predefined",
            dest="predefined",
            type=str,
            choices=self._predefined_images,
            help="Pick a predefined image",
        )
        image_create_parser.add_argument(
            "--min-vcpu",
            dest="min_vcpu",
            type=int,
            default=0,
            help="An optional number of minimum vCPUs for this image",
        )
        image_create_parser.add_argument(
            "--min-ram",
            dest="min_ram",
            type=int,
            default=0,
            help="An optional number of minimum RAM for this image",
        )
        image_create_parser.add_argument(
            "--min-ram-scale",
            dest="min_ram_scale",
            type=BinaryScale,
            default=BinaryScale.G,
            help="Scale of the minimum RAM specification",
        )
        image_create_parser.add_argument(
            "--min-disk",
            dest="min_disk",
            type=int,
            default=0,
            help="An optional number of minimum disk space for this image",
        )
        image_create_parser.add_argument(
            "--min-disk-scale",
            dest="min_disk_scale",
            type=BinaryScale,
            default=BinaryScale.G,
            help="Scale of the minimum disk space specification",
        )
        image_create_parser.set_defaults(cmd=self.create)
        image_modify_parser = image_subparser.add_parser(name="modify", help="Modify an image")
        image_modify_parser.add_argument(
            "--uid", dest="uid", type=uuid.UUID, required=True, help="The image uid"
        )
        image_modify_parser.add_argument(
            "--min-cpu",
            dest="min_cpu",
            type=int,
            required=False,
            default=None,
            help="An optional number of minimum vCPUs for this image",
        )
        image_modify_parser.add_argument(
            "--min-ram",
            dest="min_ram",
            type=int,
            required=False,
            default=None,
            help="An optional number of minimum RAM (in MB) for this image",
        )
        image_modify_parser.add_argument(
            "--min-ram-scale",
            dest="min_ram_scale",
            type=BinaryScale,
            required=False,
            default=BinaryScale.G,
            help="Scale of the minimum RAM specification",
        )
        image_modify_parser.add_argument(
            "--min-disk",
            dest="min_disk",
            type=int,
            required=False,
            default=0,
            help="An optional number of minimum disk space for this image",
        )
        image_modify_parser.add_argument(
            "--min-disk-scale",
            dest="min_disk_scale",
            type=BinaryScale,
            required=False,
            default=BinaryScale.G,
            help="Scale of the minimum disk space specification",
        )
        image_modify_parser.set_defaults(cmd=self.modify)
        image_remove_parser = image_subparser.add_parser(name="remove", help="Remove an image")
        image_remove_parser.add_argument(
            "--uid", dest="uid", type=uuid.UUID, required=True, help="The image uid"
        )
        image_remove_parser.set_defaults(cmd=self.remove)

    def create(self, args: argparse.Namespace) -> int:
        if args.url is None:
            predefined_image = list(
                filter(lambda pi: pi.name == args.predefined, Predefined_Images)
            )
            url = predefined_image[0].url
        else:
            url = args.url
        schema = ImageCreateSchema(
            name=args.name,
            url=url,
            min_vcpu=args.min_vcpu,
            min_ram=BinarySizedValue(value=args.min_ram, scale=args.min_ram_scale),
            min_disk=BinarySizedValue(value=args.min_disk, scale=args.min_disk_scale),
        )
        if args.url:
            schema.url = args.url
        resp = self._api_client(
            uri="/api/images/",
            method="POST",
            schema=schema,
            expected_status=[201],
            fallback_msg="Failed to download image",
        )
        if not resp:
            return 1
        task = TaskGetSchema.model_validate(resp.json())
        with rich.progress.Progress() as progress:
            download_task = progress.add_task(
                f"[green]Download image {args.name}...", total=100, visible=True
            )
            while not task.state == TaskState.DONE:
                resp = self._api_client(
                    uri=f"/api/tasks/{task.uid}",
                    expected_status=[200],
                    fallback_msg=f"Failed to fetch status for task {task.uid}",
                )
                if not resp:
                    return 1
                task = TaskGetSchema.model_validate(resp.json())
                if task.state == TaskState.FAILED:
                    progress.update(
                        download_task,
                        completed=100,
                        refresh=True,
                        description=f"Failed: {task.msg}",
                        visible=False,
                    )
                    console.print(f"[red]ERROR[/red]: {task.msg}")
                    return 1
                else:
                    progress.update(download_task, completed=task.percent_complete, refresh=True)
                time.sleep(2)
        return 0

    def modify(self, args: argparse.Namespace) -> int:
        schema = ImageModifySchema(
            name=args.name or None,
            min_vcpu=args.min_cpu or -1,
            min_ram=BinarySizedValue(value=args.min_ram, scale=args.min_ram_scale),
            min_disk=BinarySizedValue(value=args.min_disk, scale=args.min_disk_scale),
        )
        resp = self._api_client(
            uri=f"/api/images/{args.uid}",
            method="PUT",
            schema=schema,
            expected_status=[200],
            fallback_msg="Failed to modify image",
        )
        if not resp:
            return 1
        image = ImageGetSchema.model_validate_json(resp.content)
        console.print(image)
        return 0
