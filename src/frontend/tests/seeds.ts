import { BootstrapGetSchema, BootstrapKind, BootstrapListSchema } from "@/store/bootstraps";
import { TaskGetSchema, TaskListSchema, TaskRelation, TaskState } from "@/store/tasks";
import { NetworkGetSchema, NetworkKind, NetworkListSchema } from "@/store/networks";

export const bootstrapSeed: BootstrapListSchema = {
  entries: [
    new BootstrapGetSchema("0", "bootstrap 0", BootstrapKind.IGNITION, "foo", []),
    new BootstrapGetSchema("1", "bootstrap 1", BootstrapKind.IGNITION, "meh", ["bar"]),
    new BootstrapGetSchema("2", "bootstrap 2", BootstrapKind.CLOUD_INIT, "quux"),
  ],
};
export const taskSeed: TaskListSchema = {
  entries: [
    new TaskGetSchema("0", "task zero", TaskRelation.BOOTSTRAPS, TaskState.RUNNING, "foo", 10, ""),
    new TaskGetSchema(
      "1",
      "task one",
      TaskRelation.INSTANCES,
      TaskState.DONE,
      "created instance",
      100,
      "",
    ),
    new TaskGetSchema(
      "2",
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
