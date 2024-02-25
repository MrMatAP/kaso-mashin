import pytest
import pathlib

from kaso_mashin.common.base_types import BinaryScale, BinarySizedValue, DiskFormat
from kaso_mashin.common.entities.disks import DiskEntity, DiskModel, DiskAggregateRoot, DiskCreateSchema, DiskModifySchema


@pytest.mark.asyncio(scope='module')
async def test_async_disks(async_sessionmaker):
    disk_aggregate_root = DiskAggregateRoot(model=DiskModel, session_maker=async_sessionmaker)
    try:
        disk = await DiskEntity.create(owner=disk_aggregate_root,
                                       name='Test Disk',
                                       path=pathlib.Path(__file__).parent / 'build' / 'test-disk-0.qcow2',
                                       size=BinarySizedValue(1, BinaryScale.M))

        loaded = await disk_aggregate_root.get(disk.uid)
        assert disk == loaded
        await disk.resize(BinarySizedValue(2, scale=BinaryScale.M))
        updated = await disk_aggregate_root.get(disk.uid, force_reload=True)
        assert disk.size == updated.size
        assert disk == updated
        listed = await disk_aggregate_root.list()
        assert len(listed) == 1
        assert disk == listed[0]

        for i in range(1, 10):
            await DiskEntity.create(owner=disk_aggregate_root,
                                    name=f'Test Disk {i}',
                                    path=pathlib.Path(__file__).parent / 'build' / f'test-disk-{i}.qcow2',
                                    size=BinarySizedValue(1, BinaryScale.M))
        entities = await disk_aggregate_root.list()
        assert len(entities) == 10

        schema_list = await disk_aggregate_root.list_schema()
        assert len(entities) == len(schema_list)

        schema_get = disk.schema_get()
        assert schema_get.uid == disk.uid
        assert schema_get.name == disk.name
        assert schema_get.path == disk.path
        assert schema_get.size == disk.size
        assert schema_get.disk_format == disk.disk_format

        schema_create = DiskCreateSchema(name='Test Disk Schema',
                                         path=pathlib.Path(__file__).parent / 'build' / f'test-disk-schema.qcow2',
                                         size=BinarySizedValue(1, BinaryScale.M),
                                         disk_format=DiskFormat.QCoW2)
        schema_disk = await DiskEntity.schema_create(disk_aggregate_root, schema_create)
        assert schema_disk.uid is not None
        assert schema_disk.name == schema_create.name
        assert schema_disk.path == schema_create.path
        assert schema_disk.size == schema_create.size
        assert schema_disk.disk_format == schema_create.disk_format

        schema_modify = DiskModifySchema(size=BinarySizedValue(2, BinaryScale.M))
        await schema_disk.schema_modify(schema_modify)
        assert schema_disk.size == schema_modify.size
    finally:
        disks = await disk_aggregate_root.list(force_reload=True)
        for disk in disks:
            await disk.remove()
            assert not disk.path.exists()
        assert len(await disk_aggregate_root.list()) == 0
