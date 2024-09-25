import asyncio

import ipaddress
import pathlib
import re
import shutil
import subprocess
import typing

import aiofiles
import httpx

import jinja2
import jinja2.meta

from .types import (
    BinaryScale,
    BinarySizedValue,
    IdentityKind,
    DiskFormat,
    NetworkKind,
    BootstrapKind, \
    InstanceState)
from .exceptions import (
    EntityInvariantException,
    EntityNotFoundException,
    BootstrapException,
    DiskException,
    ImageException,
    InstanceException
)
from .base import (
    UniqueIdentifier,
    Entity,
    AggregateRoot
)
from .model import InstanceModel
from .schema import (
    DiskModifySchema,
    ImageModifySchema,
    InstanceModifySchema,
    NetworkModifySchema
)

from kaso_mashin.common.types import DEFAULT_MIN_VCPU, DEFAULT_MIN_RAM, DEFAULT_MIN_DISK, \
    DEFAULT_MAC_PREFIX
from .services import Task
from . import TaskState


class Identity(AggregateRoot):
    """
    Domain model entity for an identity
    """

    def __init__(self, name: str, kind: IdentityKind = IdentityKind.PUBKEY):
        super().__init__(name)
        self._kind = kind
        self._gecos: str = 'Someone'
        self._homedir: pathlib.Path = pathlib.Path(f'/home/{name.replace(" ", "_")}')
        self._shell: str = '/bin/bash'
        self._credential: str = ''

    @property
    def kind(self) -> IdentityKind:
        return self._kind

    @property
    def gecos(self) -> str:
        return self._gecos

    @gecos.setter
    def gecos(self, value: str) -> None:
        self._gecos = value
        self._dirty = True

    @property
    def homedir(self) -> pathlib.Path:
        return self._homedir

    @homedir.setter
    def homedir(self, value: pathlib.Path) -> None:
        self._homedir = value
        self._dirty = True

    @property
    def shell(self) -> str:
        return self._shell

    @shell.setter
    def shell(self, value: str) -> None:
        self._shell = value
        self._dirty = True

    @property
    def credential(self) -> str:
        return self._credential

    @credential.setter
    def credential(self, value: str) -> None:
        self._credential = value
        self._dirty = True

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self._kind == other.kind,
            self._gecos == other.gecos,
            self._homedir == other.homedir,
            self._shell == other.shell,
            self._credential == other.credential
        ])


class Image(AggregateRoot):
    """
    Domain model entity for an image
    """

    def __init__(
            self,
            name: str,
            url: str,
            path: pathlib.Path
    ):
        super().__init__(name)
        self._url: str = url
        self._path: pathlib.Path = path
        self._min_vcpu: int = 0
        self._min_ram = BinarySizedValue(value=0, scale=BinaryScale.G)
        self._min_disk = BinarySizedValue(value=0, scale=BinaryScale.G)
        self._disks: typing.List['Disk'] = []

    @property
    def url(self) -> str:
        return self._url

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def min_vcpu(self) -> int:
        return self._min_vcpu

    @min_vcpu.setter
    def min_vcpu(self, value: int) -> None:
        self._min_vcpu = value
        self._dirty = True

    @property
    def min_ram(self) -> BinarySizedValue:
        return self._min_ram

    @min_ram.setter
    def min_ram(self, value: BinarySizedValue) -> None:
        self._min_ram = value
        self._dirty = True

    @property
    def min_disk(self) -> BinarySizedValue:
        return self._min_disk

    @min_disk.setter
    def min_disk(self, value: BinarySizedValue) -> None:
        self._min_disk = value
        self._dirty = True

    @property
    def disks(self) -> typing.List['Disk']:
        return self._disks

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self._url == other.url,
            self._path == other.path,
            self._min_vcpu == other.min_vcpu,
            self._min_ram == other.min_ram,
            self._min_disk == other.min_disk,
            self._disks == other.disks])

    async def post_create(self) -> None:
        try:
            if self.path.exists():
                raise ImageException(status=400, msg=f'Image at {self.path} already exists')
            self.path.parent.mkdir(parents=True, exist_ok=True)

            class DownloadTask(Task):
                async def run(self, url: str, path: pathlib.Path):
                    try:
                        await super().run()
                        resp = httpx.head(url, follow_redirects=True, timeout=60)
                        size = int(resp.headers.get('content-length'))
                        client = httpx.AsyncClient(follow_redirects=True, timeout=60)
                        chunk_size = 32784
                        current = 0
                        async with (client.stream('GET', url=url) as resp,
                                    aiofiles.open(path, mode='wb') as image_file):
                            async for chunk in resp.aiter_bytes(chunk_size):
                                await image_file.write(chunk)
                                current += chunk_size
                                await self.progress(int(current / size * 100),
                                                    msg='Downloading image')
                        await self.done('Image downloaded')
                    except asyncio.CancelledError:
                        self._state = TaskState.CANCELLED
                        path.unlink(missing_ok=True)

            t = self.task_service.create(DownloadTask(name=f'Download Image {self.name}'),
                                         url=self.url,
                                         path=self.path)
            await t.task
            await super().post_create()
        except PermissionError as pe:
            raise ImageException(status=400,
                                 msg=f'No permission to save the image at {self.path}') from pe

    async def pre_remove(self) -> None:
        try:
            if len(self.disks) > 0:
                raise EntityInvariantException(status=400, msg='There are disks using this image as backing store')
            self.path.unlink(missing_ok=True)
            return await super().pre_remove()
        except PermissionError as pe:
            raise ImageException(status=400,
                                 msg=f'No permission to remove the image at {self.path}') from pe


class Disk(AggregateRoot):
    """
    Domain model entity for a disk
    """

    def __init__(
            self,
            name: str,
            path: pathlib.Path,
            size: BinarySizedValue = BinarySizedValue(2, BinaryScale.G),
            disk_format: DiskFormat = DiskFormat.Raw,
            image: Image | None = None,
    ) -> None:
        super().__init__(name)
        self._path = path
        self._size = size
        self._disk_format = disk_format
        self._image = image

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def size(self) -> BinarySizedValue:
        return self._size

    @size.setter
    def size(self, value: BinarySizedValue) -> None:
        self._size = value
        self._dirty = True

    @property
    def disk_format(self) -> DiskFormat:
        return self._disk_format

    @property
    def image(self) -> Image:
        return self._image

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self._name == other.name,
            self._path == other.path,
            self._size == other.size,
            self._disk_format == other.disk_format,
            self._image == other.image,
        ])

    def __repr__(self) -> str:
        return (
            f"DiskEntity(uid={self.uid}, "
            f"name={self.name}, "
            f"path={self.path}, "
            f"size={self.size}, "
            f"disk_format={self.disk_format},"
            f"image={self.image})"
        )

    async def post_create(self) -> None:
        try:
            if self.path.exists():
                raise DiskException(status=400, msg=f'Disk at {self.path} already exists')
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.image is not None and self.size < self.image.min_disk:
                raise DiskException(status=400, msg=f"Disk size is less than image minimum size")

            class CreateDiskTask(Task):
                async def run(self,
                              path: pathlib.Path,
                              size: BinarySizedValue,
                              disk_format: DiskFormat,
                              image: Image) -> None:
                    try:
                        args = ["/opt/homebrew/bin/qemu-img", "create", "-q", "-f", str(disk_format)]
                        if image is not None:
                            args.extend(["-F", str(disk_format), "-b", str(image.path)])
                        args.extend([str(path), str(size)])
                        subprocess.run(args, check=True)
                        await self.done('Disk created')
                    except subprocess.CalledProcessError as cpe:
                        await self.fail(f'Failed to create disk: {cpe}')
                    except asyncio.CancelledError:
                        self._state = TaskState.CANCELLED
                        path.unlink(missing_ok=True)

            t = self.task_service.create(CreateDiskTask(name=f'Create Disk {self.name}'),
                                         path=self.path,
                                         size=self.size,
                                         disk_format=self.disk_format,
                                         image=self.image)
            await t.task
            if self.image is not None:
                self.image.disks.append(self)
            await super().post_create()
        except PermissionError as pe:
            raise DiskException(status=400,
                                msg=f'No permission to create the disk at {self.path}') from pe

    async def post_modify(self) -> None:
        try:
            class ResizeTask(Task):
                async def run(self,
                              path: pathlib.Path,
                              disk_format: DiskFormat,
                              current: BinarySizedValue,
                              new: BinarySizedValue):
                    try:
                        await super().run()
                        args = ["/opt/homebrew/bin/qemu-img", "resize", "-q", "-f", str(disk_format)]
                        if current > new:
                            args.append("--shrink")
                        args += [str(path), str(new)]
                        subprocess.run(args, check=True)
                        await self.done('Successfully resized the disk')
                    except subprocess.CalledProcessError as cpe:
                        await self.fail(f'Failed to resize disk: {cpe.output}')
                    except asyncio.CancelledError:
                        self._state = TaskState.CANCELLED
                        path.unlink(missing_ok=True)

            current_size = BinarySizedValue(self.path.stat().st_size, BinaryScale.b)
            if current_size != self._size:
                t = self.task_service.create(ResizeTask(name=f'Resize disk {self.name}'),
                                             path=self.path,
                                             disk_format=self.disk_format,
                                             current=current_size,
                                             new=self._size)
                await t.task
            await super().post_modify()
        except PermissionError as pe:
            raise DiskException(status=400,
                                msg=f'No permission to resize image {self.name}') from pe
        return await super().post_modify()

    async def pre_remove(self) -> None:
        try:
            # TODO: Check whether we have instances dependending on this disk
            self.path.unlink(missing_ok=True)
            if self.image is not None:
                self.image.disks.remove(self)
            return await super().pre_remove()
        except PermissionError as pe:
            raise DiskException(status=400,
                                msg=f'No permission to remove the disk at {self.path}') from pe


class NetworkEntity(Entity):
    """
    Domain model entity for a network
    """

    def __init__(
            self,
            name: str,
            kind: NetworkKind,
            cidr: ipaddress.IPv4Network,
            gateway: ipaddress.IPv4Address
    ):
        super().__init__(name)
        self._kind = kind
        self._cidr = cidr
        self._gateway = gateway
        if cidr.num_addresses < 4:
            raise EntityInvariantException(status=400,
                                           msg='A network must have at least one free IP address')
        self._dhcp_start = cidr.network_address + 2
        self._dhcp_end = cidr.broadcast_address - 1

    @property
    def kind(self) -> NetworkKind:
        return self._kind

    @property
    def cidr(self) -> ipaddress.IPv4Network:
        return self._cidr

    @property
    def netmask(self) -> ipaddress.IPv4Address:
        return self._cidr.netmask

    @property
    def gateway(self) -> ipaddress.IPv4Address:
        return self._gateway

    @property
    def dhcp_start(self) -> ipaddress.IPv4Address:
        return self._dhcp_start

    @dhcp_start.setter
    def dhcp_start(self, value: ipaddress.IPv4Address) -> None:
        if value not in self._cidr:
            raise EntityInvariantException(status=400,
                                           msg='The DHCP start address must be within the network')
        self._dhcp_start = value
        self._dirty = True

    @property
    def dhcp_end(self) -> ipaddress.IPv4Address:
        return self._dhcp_end

    @dhcp_end.setter
    def dhcp_end(self, value: ipaddress.IPv4Address) -> None:
        if value not in self._cidr:
            raise EntityInvariantException(status=400,
                                           msg='The DHCP end address must be within the network')
        self._dhcp_end = value
        self._dirty = True

    def __eq__(self, other: typing.Any) -> bool:
        return all([
            super().__eq__(other),
            self.name == other.name,
            self.kind == other.kind,
            self.cidr == other.cidr,
            self.gateway == other.gateway,
            self.dhcp_start == other.dhcp_start,
            self.dhcp_end == other.dhcp_end,
        ])

    @staticmethod
    async def create(
            name: str,
            kind: NetworkKind,
            cidr: ipaddress.IPv4Network,
            gateway: ipaddress.IPv4Address,
            dhcp_start: ipaddress.IPv4Address | None = None,
            dhcp_end: ipaddress.IPv4Address | None = None,
    ) -> "NetworkEntity":
        if dhcp_start is None or dhcp_end is None:
            network = ipaddress.IPv4Network(cidr)
            hosts = list(network.hosts())
            dhcp_start = hosts[2] or dhcp_start
            dhcp_end = hosts[-1] or dhcp_end
        network = NetworkEntity(
            name=name,
            kind=kind,
            cidr=cidr,
            gateway=gateway)
        network.dhcp_start = dhcp_start
        network.dhcp_end = dhcp_end
        await NetworkEntity.repository.create(network)
        return network

    async def modify(self, schema: NetworkModifySchema) -> "NetworkEntity":
        if schema.name is not None:
            self._name = schema.name
        if schema.cidr is not None:
            self._cidr = schema.cidr
        if schema.gateway is not None:
            self._gateway = schema.gateway
        if schema.dhcp_start is not None:
            self._dhcp_start = schema.dhcp_start
        if schema.dhcp_end is not None:
            self._dhcp_end = schema.dhcp_end
        return await self.repository.modify(self)

    async def remove(self):
        await NetworkEntity.repository.remove(self)


class BootstrapEntity(Entity):
    """
    Domain model entity for bootstrap
    """

    def __init__(self, name: str, kind: BootstrapKind, content: str):
        super().__init__(name)
        self._kind = kind
        self.content = content

    @property
    def kind(self) -> BootstrapKind:
        return self._kind

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value
        self._template = jinja2.Environment(enable_async=True).from_string(self._content)
        ast = jinja2.Environment().parse(self._content)
        self._required_keys = jinja2.meta.find_undeclared_variables(ast)
        self._dirty = True

    @property
    def required_keys(self) -> typing.Set:
        return self._required_keys

    async def render(self, kv: typing.Dict[str, typing.Any], bootstrap_file: pathlib.Path):
        try:
            rendered = await self._template.render_async(kv)
            if self.kind == BootstrapKind.IGNITION:
                bootstrap_file_source = bootstrap_file.parent.joinpath("bootstrap.yaml")
                bootstrap_file_source.write_text(rendered)
                args = [
                    self.runtime.config.butane_path,
                    "-p",
                    "-o",
                    bootstrap_file,
                    bootstrap_file_source,
                ]
                subprocess.run(args, check=True)
            else:
                bootstrap_file.write_text(rendered, encoding="utf-8")
        except jinja2.TemplateError as te:
            raise BootstrapException(status=400, msg="Templating error") from te
        except subprocess.CalledProcessError as e:
            raise BootstrapException(status=500, msg="Failed to render bootstrap") from e
        except Exception as e:
            raise BootstrapException(status=500, msg="Unknown error") from e

    def __eq__(self, other: "BootstrapEntity") -> bool:
        return all(
            [
                super().__eq__(other),
                self.name == other.name,
                self.kind == other.kind,
                self.content == other.content,
            ]
        )

    @staticmethod
    async def create(name: str, kind: BootstrapKind, content: str) -> "BootstrapEntity":
        bootstrap = BootstrapEntity(name=name, kind=kind, content=content)
        await BootstrapEntity.repository.create(bootstrap)
        return bootstrap

    async def modify(self, name: str, kind=kind, content=content):
        self._name = name
        self._kind = kind
        self._content = content
        await self.repository.modify(self)

    async def remove(self):
        await self.repository.remove(self)


class InstanceEntity(Entity):
    """
    Domain model entity for an instance
    """

    def __init__(
            self,
            name: str,
            path: pathlib.Path,
            uefi_code: pathlib.Path,
            uefi_vars: pathlib.Path,
            vcpu: int,
            ram: BinarySizedValue,
            image: Image,
            os_disk: Disk,
            network: NetworkEntity,
            bootstrap: BootstrapEntity,
            bootstrap_file: pathlib.Path,
    ):
        super().__init__(name)
        self._path = path
        self._uefi_code = uefi_code
        self._uefi_vars = uefi_vars
        self._vcpu = vcpu
        self._ram = ram
        self._mac = self._generate_mac()
        self._image = image
        self._os_disk = os_disk
        self._network = network
        self._bootstrap = bootstrap
        self._bootstrap_file = bootstrap_file
        self._popen = None
        self._state = InstanceState.STOPPED

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def vcpu(self) -> int:
        return self._vcpu

    @property
    def ram(self) -> BinarySizedValue:
        return self._ram

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def image_uid(self) -> UniqueIdentifier:
        return self._image.uid

    @property
    def os_disk_uid(self) -> UniqueIdentifier:
        return self._os_disk.uid

    @property
    def os_disk_size(self) -> BinarySizedValue:
        return self._os_disk.size

    @property
    def network_uid(self) -> UniqueIdentifier:
        return self._network.uid

    @property
    def bootstrap_uid(self) -> UniqueIdentifier:
        return self._bootstrap.uid

    @property
    def bootstrap_file(self) -> pathlib.Path:
        return self._bootstrap_file

    @property
    def state(self) -> InstanceState:
        return self._state

    # TODO: Consider replacing this in favour of image_uid
    @property
    def image(self) -> Image:
        return self._image

    # TODO: Consider replacing this in favour of os_disk_uid
    @property
    def os_disk(self) -> Disk:
        return self._os_disk

    # TODO: Consider replacing this in favour of network_uid
    @property
    def network(self) -> NetworkEntity:
        return self._network

    # TODO: Consider replacing this in favour of bootstrap_uid
    @property
    def bootstrap(self) -> BootstrapEntity:
        return self._bootstrap

    # TODO: Consider moving this into bootstrap
    @property
    def uefi_code(self) -> pathlib.Path:
        return self._uefi_code

    # TODO: Consider moving this into bootstrap
    @property
    def uefi_vars(self) -> pathlib.Path:
        return self._uefi_vars

    def __eq__(self, other: "InstanceEntity") -> bool:
        return all(
            [
                super().__eq__(other),
                self.name == other.name,
                self.path == other.path,
                self.uefi_code == other.uefi_code,
                self.uefi_vars == other.uefi_vars,
                self.vcpu == other.vcpu,
                self.ram == other.ram,
                self.mac == other.mac,
                self.image == other.image,
                self.os_disk == other.os_disk,
                self.network == other.network,
                self.bootstrap == other.bootstrap,
                self.bootstrap_file == other.bootstrap_file,
            ]
        )

    @staticmethod
    async def from_model(model: InstanceModel) -> "InstanceEntity":
        # TODO: Internal consistency. This will fail if the disk is dead
        image = await Image.repository.get_by_uid(UniqueIdentifier(model.image_uid))
        os_disk = await Disk.repository.get_by_uid(UniqueIdentifier(model.os_disk_uid))
        network = await NetworkEntity.repository.get_by_uid(UniqueIdentifier(model.network_uid))
        bootstrap = await BootstrapEntity.repository.get_by_uid(
            UniqueIdentifier(model.bootstrap_uid)
        )

        entity = InstanceEntity(
            name=model.name,
            path=pathlib.Path(model.path),
            uefi_code=pathlib.Path(model.uefi_code),
            uefi_vars=pathlib.Path(model.uefi_vars),
            vcpu=model.vcpu,
            ram=BinarySizedValue(value=model.ram, scale=BinaryScale(model.ram_scale)),
            image=image,
            os_disk=os_disk,
            network=network,
            bootstrap=bootstrap,
            bootstrap_file=pathlib.Path(model.bootstrap_file),
        )
        entity._uid = UniqueIdentifier(model.uid)
        entity._mac = model.mac
        return entity

    async def to_model(self, model: InstanceModel | None = None) -> InstanceModel:
        if model is None:
            return InstanceModel(
                uid=str(self.uid),
                name=self.name,
                path=str(self.path),
                uefi_code=str(self.uefi_code),
                uefi_vars=str(self.uefi_vars),
                vcpu=self.vcpu,
                ram=self.ram.value,
                ram_scale=self.ram.scale,
                mac=self.mac,
                image_uid=str(self.image_uid),
                os_disk_uid=str(self.os_disk_uid),
                network_uid=str(self.network_uid),
                bootstrap_uid=str(self.bootstrap_uid),
                bootstrap_file=str(self.bootstrap_file),
            )
        else:
            model.uid = str(self.uid)
            model.name = self.name
            model.path = str(self.path)
            model.uefi_code = str(self.uefi_code)
            model.uefi_vars = str(self.uefi_vars)
            model.vcpu = self.vcpu
            model.ram = self.ram.value
            model.ram_scale = self.ram.scale
            model.mac = str(self.mac)
            model.os_disk_uid = str(self.os_disk_uid)
            model.network_uid = str(self.network_uid)
            model.bootstrap_uid = str(self.bootstrap_uid)
            model.bootstrap_file = str(self.bootstrap_file)
            return model

    def _generate_mac(self) -> str:
        octets = re.findall("..", self.uid.hex[:6])
        return f'{DEFAULT_MAC_PREFIX}:{":".join(octets)}'

    @staticmethod
    async def create(
            task: Task,
            user: str,
            name: str,
            path: pathlib.Path,
            uefi_code: pathlib.Path,
            uefi_vars: pathlib.Path,
            vcpu: int,
            ram: BinarySizedValue,
            image: Image,
            os_disk_size: BinarySizedValue,
            network: NetworkEntity,
            bootstrap: BootstrapEntity,
    ) -> "InstanceEntity":
        if path.exists():
            raise InstanceException(
                status=400, msg=f"Instance path at {path} already exists", task=task
            )
        os_disk = None
        try:
            path.mkdir(parents=True, exist_ok=True)
            shutil.chown(path=path, user=user)

            instance_uefi_code = path / "uefi_code.fd"
            instance_uefi_code.symlink_to(uefi_code)
            instance_uefi_vars = path / "uefi_vars.fd"
            shutil.copyfile(uefi_vars, instance_uefi_vars)

            os_disk = await Disk.create(
                name="OS Disk 0",
                path=path / "os.qcow2",
                size=os_disk_size,
                disk_format=DiskFormat.QCoW2,
                image=image,
            )

            bootstrap_file = path / "bootstrap.json"
            await bootstrap.render(bootstrap_file=bootstrap_file, kv={"name": name})

            entity = InstanceEntity(
                name=name,
                path=path,
                uefi_code=instance_uefi_code,
                uefi_vars=instance_uefi_vars,
                vcpu=vcpu,
                ram=ram,
                image=image,
                os_disk=os_disk,
                network=network,
                bootstrap=bootstrap,
                bootstrap_file=bootstrap_file,
            )

            outcome = await InstanceEntity.repository.create(entity)
            await task.done(msg="Successfully created", outcome=outcome.uid)
            return outcome
        except Exception as e:
            if os_disk_size is not None:
                await os_disk.remove()
            await task.fail(msg=f"Some exception {e} occurred")
            shutil.rmtree(path)
            raise InstanceException(status=400, msg=f"Some exception {e}")

    async def modify(self, schema: InstanceModifySchema, task: Task):
        if schema.state == InstanceState.STARTED:
            await self.start()
        if schema.state == InstanceState.STOPPED:
            await self.stop()
        await task.done(msg="Successfully modified")

    async def start(self):
        try:
            self._popen = self.runtime.qemu_service.start_instance(self)
            self._state = InstanceState.STARTED
        except Exception as e:
            pass

    async def stop(self):
        if self._popen is None:
            return
        self._popen.terminate()
        self._state = InstanceState.STOPPED

    async def remove(self):
        await self.stop()
        shutil.rmtree(self.path)
        await InstanceEntity.repository.remove(self)
