import pytest
import pathlib

from kaso_mashin.common.base_types import BinaryScale, BinarySizedValue

from kaso_mashin.common.entities import (
    TaskRepository, TaskEntity, TaskModel, TaskState,
    DiskRepository, DiskEntity, DiskModel,
    ImageRepository, ImageEntity, ImageModel
)


@pytest.mark.asyncio(scope='module')
async def test_async_disks(async_sessionmaker):
    disk_aggregate_root = DiskRepository(session_maker=async_sessionmaker,
                                         aggregate_root_class=DiskEntity,
                                         model_class=DiskModel)
    try:
        disk = await DiskEntity.create(name='Test Disk',
                                       path=pathlib.Path(__file__).parent / 'build' / 'test-disk-0.qcow2',
                                       size=BinarySizedValue(1, BinaryScale.M))

        loaded = await disk_aggregate_root.get_by_uid(disk.uid)
        assert disk == loaded
        await disk.resize(BinarySizedValue(2, scale=BinaryScale.M))
        updated = await disk_aggregate_root.get_by_uid(disk.uid)
        assert disk.size == updated.size
        assert disk == updated
        listed = await disk_aggregate_root.list()
        assert len(listed) == 1
        assert disk == listed[0]

        for i in range(1, 10):
            await DiskEntity.create(name=f'Test Disk {i}',
                                    path=pathlib.Path(__file__).parent / 'build' / f'test-disk-{i}.qcow2',
                                    size=BinarySizedValue(1, BinaryScale.M))
        entities = await disk_aggregate_root.list()
        assert len(entities) == 10
    finally:
        disks = await disk_aggregate_root.list()
        for disk in disks:
            await disk.remove()
            assert not disk.path.exists()
        assert len(await disk_aggregate_root.list()) == 0


@pytest.mark.asyncio(scope='module')
async def test_async_images(async_sessionmaker):
    task_aggregate_root = TaskRepository(session_maker=async_sessionmaker,
                                         aggregate_root_class=TaskEntity,
                                         model_class=TaskModel)
    image_aggregate_root = ImageRepository(session_maker=async_sessionmaker,
                                           aggregate_root_class=ImageEntity,
                                           model_class=ImageModel)
    try:
        task = await TaskEntity.create(name='Test Task')
        image = await ImageEntity.create(name='Test Image',
                                         url='https://stable.release.flatcar-linux.net/arm64-usr/current/flatcar_production_qemu_uefi_image.img',
                                         path=pathlib.Path(__file__).parent / 'build' / 'test-image-0.qcow2',
                                         task=task,
                                         user='imfeldma')
        loaded = await image_aggregate_root.get_by_uid(image.uid)
        assert image == loaded

        entities = await image_aggregate_root.list()
        assert len(entities) == 1
    finally:
        images = await image_aggregate_root.list()
        for image in images:
            await image.remove()
            assert not image.path.exists()
        assert len(await image_aggregate_root.list()) == 0


@pytest.mark.asyncio(scope='module')
async def test_async_tasks(async_sessionmaker):
    task_aggregate_root = TaskRepository(session_maker=async_sessionmaker,
                                         aggregate_root_class=TaskEntity,
                                         model_class=TaskModel)
    try:
        task = await TaskEntity.create(name='Test Task')
        assert task.state == TaskState.RUNNING
    finally:
        tasks = await task_aggregate_root.list(force_reload=True)
