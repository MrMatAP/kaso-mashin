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
    finally:
        disks = await disk_aggregate_root.list(force_reload=True)
        for disk in disks:
            await disk.remove()
            assert not disk.path.exists()
        assert len(await disk_aggregate_root.list()) == 0
