import pathlib
import ipaddress

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .base import (
    UniqueIdentifier,
    BinarySizedValue, BinaryScale,
    KasoMashinException,
    Repository,
)
from .model import (
    IdentityModel,
    ImageModel,
    DiskModel,
    NetworkModel,
    BootstrapModel,
    InstanceModel
)
from .domain import (
    Identity,
    Image,
    Disk,
    Network,
    Bootstrap,
    Instance
)


class IdentityRepository(Repository[Identity, IdentityModel]):
    """
    A repository of identities
    """
    entity_class = Identity
    model_class = IdentityModel

    @classmethod
    async def from_model(cls, model: IdentityModel, *args, **kwargs) -> Identity:
        kwargs['kind'] = model.kind
        entity = await super().from_model(model, *args, **kwargs)
        entity.gecos = model.gecos
        entity.homedir = pathlib.Path(model.homedir)
        entity.shell = model.shell
        entity.credential = model.credential
        entity.dirty = False
        return entity

    @classmethod
    async def to_model(cls, entity: Identity, persisted: IdentityModel | None = None) -> IdentityModel:
        model = await super().to_model(entity, persisted)
        model.kind = entity.kind
        model.gecos = entity.gecos
        model.homedir = str(entity.homedir)
        model.shell = entity.shell
        model.credential = entity.credential
        return model


class ImageRepository(Repository[Image, ImageModel]):
    """
    A repository of images
    """
    entity_class = Image
    model_class = ImageModel

    @classmethod
    async def from_model(cls, model: ImageModel, *args, **kwargs) -> Image:
        kwargs['url'] = model.url
        kwargs['path'] = pathlib.Path(model.path)
        entity = await super().from_model(model, *args, **kwargs)
        entity.min_vcpu = model.min_vcpu
        entity.min_ram = BinarySizedValue(value=model.min_ram, scale=BinaryScale(model.min_ram_scale))
        entity.min_disk = BinarySizedValue(value=model.min_disk, scale=BinaryScale(model.min_disk_scale))
        if model.disks is not None:
            for disk in model.disks:
                entity.disks.append(await Disk.repository.get_by_uid(UniqueIdentifier(disk.uid)))
        entity.dirty = False
        return entity

    @classmethod
    async def to_model(cls, entity: Image, persisted: ImageModel | None = None) -> ImageModel:
        model = await super().to_model(entity, persisted)
        model.url = entity.url
        model.path = str(entity.path)
        model.min_vcpu = entity.min_vcpu
        model.min_ram = entity.min_ram.value
        model.min_ram_scale = entity.min_ram.scale
        model.min_disk = entity.min_disk.value
        model.min_disk_scale = entity.min_disk.scale
        return model


class DiskRepository(Repository[Disk, DiskModel]):
    """
    A repository of disks
    """
    entity_class = Disk
    model_class = DiskModel

    @classmethod
    async def from_model(cls, model: DiskModel, *args, **kwargs) -> Disk:
        kwargs['path'] = pathlib.Path(model.path)
        kwargs['size'] = BinarySizedValue(value=model.size, scale=BinaryScale(model.size_scale))
        kwargs['disk_format'] = model.disk_format
        if model.image is not None:
            kwargs['image'] = await Image.repository.get_by_uid(UniqueIdentifier(model.image.uid))
        return await super().from_model(model, *args, **kwargs)


    @classmethod
    async def to_model(cls, entity: Disk, persisted: DiskModel | None = None) -> DiskModel:
        model = await super().to_model(entity, persisted)
        model.path = str(entity.path)
        model.size = entity.size.value
        model.size_scale = entity.size.scale
        model.disk_format = entity.disk_format
        model.image_uid = None if entity.image is None else str(entity.image.uid)
        return model


class NetworkRepository(Repository[Network, NetworkModel]):
    """
    A repository of networks
    """
    entity_class = Network
    model_class = NetworkModel

    async def get_by_cidr(self, cidr: ipaddress.IPv4Network) -> Network:
        try:
            nets = list(filter(lambda e: e.cidr == cidr, self._identity_map.values()))
            if len(nets) > 0:
                return nets[0]
            async with self._session_maker() as session:
                model = (await session.scalars(
                            select(self.model_class))
                            .where(self.model_class.cidr == str(cidr))).one()
                return await self.from_model(model)
        except SQLAlchemyError as sae:
            raise KasoMashinException(status=500, msg='Failure getting a network by its cidr') from sae

    @classmethod
    async def from_model(cls, model: NetworkModel, *args, **kwargs) -> Network:
        kwargs['kind'] = model.kind
        kwargs['cidr'] = ipaddress.IPv4Network(model.cidr)
        kwargs['gateway'] = ipaddress.IPv4Address(model.gateway)
        entity = await super().from_model(model, *args, **kwargs)
        entity.dhcp_start = ipaddress.IPv4Address(model.dhcp_start)
        entity.dhcp_end = ipaddress.IPv4Address(model.dhcp_end)
        entity.dirty = False
        return entity

    @classmethod
    async def to_model(cls, entity: Network, persisted: NetworkModel | None = None) -> NetworkModel:
        model = await super().to_model(entity, persisted)
        model.kind = entity.kind
        model.cidr = str(entity.cidr)
        model.gateway = str(entity.gateway)
        model.dhcp_start = str(entity.dhcp_start)
        model.dhcp_end = str(entity.dhcp_end)
        return model


class BootstrapRepository(Repository[Bootstrap, BootstrapModel]):
    """
    A repository of bootstraps
    """
    entity_class = Bootstrap
    model_class = BootstrapModel

    @classmethod
    async def from_model(cls, model: BootstrapModel, *args, **kwargs) -> Bootstrap:
        kwargs['kind'] = model.kind
        kwargs['content'] = model.content
        return await super().from_model(model, *args, **kwargs)

    @classmethod
    async def to_model(cls, entity: Bootstrap, persisted: BootstrapModel | None = None) -> BootstrapModel:
        model = await super().to_model(entity, persisted)
        model.kind = entity.kind
        model.content = entity.content
        return model


class InstanceRepository(Repository[Instance, InstanceModel]):
    """
    A repository of instances
    """
    entity_class = Instance
    model_class = InstanceModel

    @classmethod
    async def from_model(cls, model: InstanceModel, *args, **kwargs) -> Instance:
        kwargs['path'] = pathlib.Path(model.path)
        kwargs['uefi_code'] = model.uefi_code
        kwargs['uefi_vars'] = model.uefi_vars
        return await super().from_model(model, *args, **kwargs)

    @classmethod
    async def to_model(cls, entity: Instance, persisted: InstanceModel | None = None) -> InstanceModel:
        pass
