import abc
import typing
import uuid
import collections
import pathlib
import shutil
import logging

import pytest
import pytest_asyncio
import tempfile

import fastapi
import fastapi.testclient

from kaso_mashin.server.run import create_server
from kaso_mashin.server.db import DB
from kaso_mashin.server.runtime import Runtime
from kaso_mashin.common import (
    UniqueIdentifier,
    BinaryScale,
    T_EntityModel,
    T_Entity,
    T_EntityListSchema,
    T_EntityGetSchema,
)
from kaso_mashin.common.config import Config
from kaso_mashin.common.entities import (
    IdentityKind,
    IdentityModel,
    DiskFormat,
    DiskModel,
    NetworkKind,
    NetworkModel,
)

KasoTestContext = collections.namedtuple("KasoTestContext", "config db runtime server client")


class BaseTest(typing.Generic[T_EntityModel, T_Entity, T_EntityGetSchema], abc.ABC):

    @staticmethod
    def find_match_in_seeds(
        uid: UniqueIdentifier, seeds: typing.List[T_EntityModel]
    ) -> T_EntityModel:
        matches = list(filter(lambda s: s.uid == str(uid), seeds))
        assert len(matches) == 1
        return matches[0]

    @abc.abstractmethod
    def assert_get_by_model(self, obj: T_EntityGetSchema | T_Entity, model: T_EntityModel):
        pass

    @abc.abstractmethod
    def assert_list_by_model(self, obj: T_EntityListSchema | T_Entity, model: T_EntityModel):
        pass


seed = {
    "identities": [
        IdentityModel(
            uid=str(uuid.uuid4()),
            name="Test Identity 1",
            kind=IdentityKind.PUBKEY,
            gecos="Test Identity 1",
            homedir="/home/test1",
            shell="/bin/bash",
            credential="ssh-rsa test1-pubkey",
        ),
        IdentityModel(
            uid=str(uuid.uuid4()),
            name="Test Identity 2",
            kind=IdentityKind.PUBKEY,
            gecos="Test Identity 2",
            homedir="/home/test2",
            shell="/bin/bash",
            credential="ssh-rsa test2-pubkey",
        ),
        IdentityModel(
            uid=str(uuid.uuid4()),
            name="Test Identity 3",
            kind=IdentityKind.PASSWORD,
            gecos="Test Identity 3",
            homedir="/home/test3",
            shell="/bin/bash",
            credential="foobar",
        ),
    ],
    "networks": [
        NetworkModel(
            uid=str(uuid.uuid4()),
            name="Test Network 1",
            kind=NetworkKind.VMNET_SHARED,
            cidr="10.0.0.0/24",
            gateway="10.0.0.1",
            dhcp_start="10.0.0.2",
            dhcp_end="10.0.0.254",
        ),
        NetworkModel(
            uid=str(uuid.uuid4()),
            name="Test Network 2",
            kind=NetworkKind.VMNET_HOST,
            cidr="10.0.1.0/24",
            gateway="10.0.1.1",
            dhcp_start="10.0.1.2",
            dhcp_end="10.0.1.254",
        ),
        NetworkModel(
            uid=str(uuid.uuid4()),
            name="Test Network 3",
            kind=NetworkKind.VMNET_BRIDGED,
            cidr="10.0.2.0/24",
            gateway="10.0.2.1",
            dhcp_start="10.0.2.2",
            dhcp_end="10.0.2.254",
        ),
    ],
    "disks": [
        DiskModel(
            uid=str(uuid.uuid4()),
            name="Test Disk 1",
            path="/no/where",
            size=1,
            size_scale=BinaryScale.M,
            disk_format=DiskFormat.Raw,
        )
    ],
}


@pytest.mark.asyncio
@pytest_asyncio.fixture(scope="session")
async def test_context_empty() -> KasoTestContext:
    """
    Fixture producing an empty Kaso test context
    """
    temp_dir = pathlib.Path(
        tempfile.mkdtemp(
            prefix="kaso-test",
            dir=pathlib.Path(__file__).parent.parent.joinpath("build"),
        )
    )
    config_file = temp_dir.joinpath(".kaso")
    with config_file.open("w", encoding="UTF-8") as c:
        c.write(f"path: {temp_dir}")
    config = Config(config_file)
    db = DB(config)
    runtime = Runtime(config=config, db=db)
    server = create_server(runtime)
    async with runtime.lifespan(app=server):
        logging.getLogger().info(f"Yielding empty Kaso Mashin context at {temp_dir}")
        yield KasoTestContext(
            config=config,
            db=db,
            runtime=runtime,
            server=server,
            client=fastapi.testclient.TestClient(server),
        )
    shutil.rmtree(temp_dir, ignore_errors=True)
    logging.getLogger().info(f"Removed empty Kaso Mashin context at {temp_dir}")


@pytest.mark.asyncio
@pytest_asyncio.fixture(scope="session")
async def test_context_seeded() -> KasoTestContext:
    """
    Fixture producing a fully seeded Kaso test context
    """
    temp_dir = pathlib.Path(
        tempfile.mkdtemp(
            prefix="kaso-test",
            dir=pathlib.Path(__file__).parent.parent.joinpath("build"),
        )
    )
    config_file = temp_dir.joinpath(".kaso")
    with config_file.open("w", encoding="UTF-8") as c:
        c.write(f"path: {temp_dir}")
    config = Config(config_file)
    db = DB(config)
    runtime = Runtime(config=config, db=db)
    server = create_server(runtime)
    session_maker = await db.async_sessionmaker
    async with session_maker() as session:
        for kind, entries in seed.items():
            for model in entries:
                session.add(model)
        await session.commit()
    async with runtime.lifespan(app=server):
        logging.getLogger().info(f"Yielding seeded Kaso Mashin context at {temp_dir}")
        yield KasoTestContext(
            config=config,
            db=db,
            runtime=runtime,
            server=server,
            client=fastapi.testclient.TestClient(server),
        )
    shutil.rmtree(temp_dir, ignore_errors=True)
    logging.getLogger().info(f"Removed seeded Kaso Mashin context at {temp_dir}")