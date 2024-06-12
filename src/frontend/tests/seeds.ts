import { BootstrapGetSchema, BootstrapKind, BootstrapListSchema } from "@/store/bootstraps";
import { TaskGetSchema, TaskListSchema, TaskRelation, TaskState } from "@/store/tasks";

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
