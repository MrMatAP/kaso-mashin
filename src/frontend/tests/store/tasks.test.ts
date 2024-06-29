import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { taskSeed } from "../seeds";
import { TaskState } from "@/store/tasks";

import {
  EntityInvariantException,
  EntityNotFoundException,
  KasoMashinException,
} from "@/base_types";

describe("Task Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached task", async ({ taskStore }) => {
    expect(taskStore.tasks.get(taskSeed.entries[0].uid)).toEqual(taskSeed.entries[0]);
    const cached_value = taskSeed.entries[0].percent_complete;
    taskSeed.entries[0].percent_complete = 80;
    expect((await taskStore.get(taskSeed.entries[0].uid)).percent_complete).toEqual(cached_value); // no forced update
  });

  storeTest("can be forced to update the task", async ({ taskStore }) => {
    expect(taskStore.tasks.get(taskSeed.entries[0].uid)).toEqual(taskSeed.entries[0]);
    taskSeed.entries[0].percent_complete = 80;
    expect((await taskStore.get(taskSeed.entries[0].uid, true)).percent_complete).toEqual(
      taskSeed.entries[0].percent_complete,
    );
    expect(taskStore.tasks.size).toBe(taskSeed.entries.length);
  });

  storeTest("correctly reports allTasks", async ({ taskStore }) => {
    expect(taskStore.allTasks.length).toBe(taskSeed.entries.length);
  });

  storeTest("correctly reports runningTasks", async ({ taskStore }) => {
    const running = taskSeed.entries.filter((task) => task.state === TaskState.RUNNING);
    expect(taskStore.runningTasks.length).toBe(running.length);
  });

  storeTest("correctly reports failedTasks", async ({ taskStore }) => {
    const failed = taskSeed.entries.filter((task) => task.state === TaskState.FAILED);
    expect(taskStore.failedTasks.length).toBe(failed.length);
  });

  storeTest("correctly reports doneTasks", async ({ taskStore }) => {
    const done = taskSeed.entries.filter((task) => task.state === TaskState.DONE);
    expect(taskStore.doneTasks.length).toBe(done.length);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ taskStore }) => {
    expect(() => taskStore.get("EntityNotFoundException")).rejects.toThrow(EntityNotFoundException);
  });

  storeTest("raises an error for a KasoMashinException", async ({ taskStore }) => {
    expect(() => taskStore.get("KasoMashinException")).rejects.toThrow(KasoMashinException);
  });
});
