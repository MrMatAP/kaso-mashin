import { defineStore } from "pinia";
import { mande } from "mande";
import { Entity } from "@/base_types";

const tasks = mande("/api/tasks/");

export enum TaskState {
  RUNNING = "running",
  DONE = "done",
  FAILED = "failed",
}

export interface TaskListSchema {
  entries: TaskGetSchema[];
}

export class TaskGetSchema extends Entity {
  state: TaskState = TaskState.RUNNING;
  msg: string = "";
  percent_complete: number = 0;
}

export const useTasksStore = defineStore("tasks", {
  state: () => ({
    tasks: [] as TaskGetSchema[],
  }),
  getters: {
    pendingNumber: (state) =>
      state.tasks.filter((task) => task.state === TaskState.RUNNING).length,
  },
  actions: {
    async list() {
      let task_list: TaskListSchema = await tasks.get();
      this.tasks = task_list.entries;
    },
    async get(uid: string): Promise<TaskGetSchema> {
      return await tasks.get(uid);
    },
  },
});
