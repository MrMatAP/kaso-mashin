import pytest
import pathlib

from kaso_mashin.common.base_types import BinaryScale, BinarySizedValue

from kaso_mashin.common.entities import (
    TaskAggregateRoot, TaskEntity, TaskModel, TaskState,
    DiskAggregateRoot, DiskEntity, DiskModel,
    ImageAggregateRoot, ImageEntity, ImageModel
)

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
    finally:
        disks = await disk_aggregate_root.list(force_reload=True)
        for disk in disks:
            await disk.remove()
            assert not disk.path.exists()
        assert len(await disk_aggregate_root.list()) == 0


@pytest.mark.asyncio(scope='module')
async def test_async_images(async_sessionmaker):
    image_aggregate_root = ImageAggregateRoot(model=ImageModel, session_maker=async_sessionmaker)
    try:
        image = await ImageEntity.create(owner=image_aggregate_root,
                                         name='Test Image',
                                         path=pathlib.Path(__file__).parent / 'build' / 'test-image-0.qcow2')
        loaded = await image_aggregate_root.get(image.uid)
        assert image == loaded

        entities = await image_aggregate_root.list()
        assert len(entities) == 1
    finally:
        images = await image_aggregate_root.list(force_reload=True)
        for image in images:
            await image.remove()
            assert not image.path.exists()
        assert len(await image_aggregate_root.list()) == 0


@pytest.mark.asyncio(scope='module')
async def test_async_tasks(async_sessionmaker):
    task_aggregate_root = TaskAggregateRoot(model=TaskModel, session_maker=async_sessionmaker)
    try:
        task = await TaskEntity.create(owner=task_aggregate_root,
                                       name='Test Task')
        assert task.state == TaskState.NEW

        await task.start()
        assert task.state == TaskState.RUNNING
    finally:
        tasks = await task_aggregate_root.list(force_reload=True)
        for task in tasks:
            await task.cancel()
            assert task.state == TaskState.CANCELLED
