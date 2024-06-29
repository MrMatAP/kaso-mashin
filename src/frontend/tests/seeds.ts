import { BootstrapGetSchema, BootstrapKind, BootstrapListSchema } from "@/store/bootstraps";
import { TaskGetSchema, TaskListSchema, TaskRelation, TaskState } from "@/store/tasks";
import { NetworkGetSchema, NetworkKind, NetworkListSchema } from "@/store/networks";
import { IdentityGetSchema, IdentityKind, IdentityListSchema } from "@/store/identities";
import { ImageGetSchema, ImageListSchema } from "@/store/images";
import { BinaryScale, BinarySizedValue } from "@/base_types";
import { DiskFormat, DiskGetSchema, DiskListSchema } from "@/store/disks";
import { InstanceGetSchema, InstanceListSchema, InstanceState } from "@/store/instances";

export const bootstrapSeed: BootstrapListSchema = {
  entries: [
    new BootstrapGetSchema(crypto.randomUUID(), "bootstrap 0", BootstrapKind.IGNITION, "foo", []),
    new BootstrapGetSchema(crypto.randomUUID(), "bootstrap 1", BootstrapKind.IGNITION, "meh", [
      "bar",
    ]),
    new BootstrapGetSchema(crypto.randomUUID(), "bootstrap 2", BootstrapKind.CLOUD_INIT, "quux"),
  ],
};

export const taskSeed: TaskListSchema = {
  entries: [
    new TaskGetSchema(
      crypto.randomUUID(),
      "task zero",
      TaskRelation.BOOTSTRAPS,
      TaskState.RUNNING,
      "foo",
      10,
      "",
    ),
    new TaskGetSchema(
      crypto.randomUUID(),
      "task one",
      TaskRelation.INSTANCES,
      TaskState.DONE,
      "created instance",
      100,
      "",
    ),
    new TaskGetSchema(
      crypto.randomUUID(),
      "task two",
      TaskRelation.IDENTITIES,
      TaskState.FAILED,
      "failed to create identity",
      10,
      "",
    ),
  ],
};

export const networkSeed: NetworkListSchema = {
  entries: [
    new NetworkGetSchema(
      crypto.randomUUID(),
      "network 0",
      NetworkKind.VMNET_HOST,
      "192.168.0.0/24",
      "192.168.0.1",
      "192.168.0.10",
      "192.168.0.254",
    ),
    new NetworkGetSchema(
      crypto.randomUUID(),
      "network 1",
      NetworkKind.VMNET_SHARED,
      "10.0.0.0/16",
      "10.0.0.1",
      "10.0.0.10",
      "10.0.0.254",
    ),
    new NetworkGetSchema(
      crypto.randomUUID(),
      "network 2",
      NetworkKind.VMNET_BRIDGED,
      "172.16.0.0/16",
      "172.16.0.1",
      "172.16.0.10",
      "172.16.0.254",
    ),
  ],
};

export const identitySeed: IdentityListSchema = {
  entries: [
    new IdentityGetSchema(
      crypto.randomUUID(),
      "identity0",
      IdentityKind.PUBKEY,
      "gecos 0",
      "/home/identity0",
      "/bin/bash",
      "MIIsecret",
    ),
    new IdentityGetSchema(
      crypto.randomUUID(),
      "identity1",
      IdentityKind.PASSWORD,
      "gecos 1",
      "/home/identity1",
      "/bin/bash",
      "",
    ),
  ],
};

export const imageSeed: ImageListSchema = {
  entries: [
    new ImageGetSchema(
      crypto.randomUUID(),
      "image 0",
      "/path/to/image0",
      "https://image0",
      1,
      new BinarySizedValue(1, BinaryScale.G),
      new BinarySizedValue(1, BinaryScale.G),
    ),
    new ImageGetSchema(
      crypto.randomUUID(),
      "image 1",
      "/path/to/image1",
      "https://image1",
      2,
      new BinarySizedValue(2, BinaryScale.G),
      new BinarySizedValue(2, BinaryScale.G),
    ),
  ],
};

export const diskSeed: DiskListSchema = {
  entries: [
    new DiskGetSchema(
      crypto.randomUUID(),
      "disk 0",
      "/path/to/disk0",
      new BinarySizedValue(1, BinaryScale.G),
      DiskFormat.QCow2,
      crypto.randomUUID(),
    ),
    new DiskGetSchema(
      crypto.randomUUID(),
      "disk 1",
      "/path/to/disk1",
      new BinarySizedValue(2, BinaryScale.G),
      DiskFormat.Raw,
    ),
    new DiskGetSchema(
      crypto.randomUUID(),
      "disk 2",
      "/path/to/disk2",
      new BinarySizedValue(3, BinaryScale.G),
      DiskFormat.VDI,
    ),
  ],
};

export const instanceSeed: InstanceListSchema = {
  entries: [
    new InstanceGetSchema(
      crypto.randomUUID(),
      "instance 0",
      "/path/to/instance0",
      1,
      new BinarySizedValue(1, BinaryScale.G),
      "00:00:00:00:00:00",
      crypto.randomUUID(),
      new BinarySizedValue(1, BinaryScale.G),
      crypto.randomUUID(),
      crypto.randomUUID(),
      "/path/to/bootstrap0",
      InstanceState.STOPPED,
    ),
    new InstanceGetSchema(
      crypto.randomUUID(),
      "instance 1",
      "/path/to/instance1",
      1,
      new BinarySizedValue(1, BinaryScale.G),
      "00:00:00:00:00:01",
      crypto.randomUUID(),
      new BinarySizedValue(1, BinaryScale.G),
      crypto.randomUUID(),
      crypto.randomUUID(),
      "/path/to/bootstrap1",
      InstanceState.STARTED,
    ),
  ],
};
