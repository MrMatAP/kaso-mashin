import { defineStore } from "pinia";
import { mande } from "mande";

const tasks = mande("/api/tasks/");

export enum TaskState {
  RUNNING = "running",
  DONE = "done",
  FAILED = "failed",
}

export interface TaskListSchema {
  entries: TaskGetSchema[];
}

export class TaskGetSchema {
  readonly uid: string = "";
  name: string = "";
  state: TaskState = TaskState.RUNNING;
  msg: string = "";
  percent_complete: number = 0;
}

export const useTasksStore = defineStore("images", {
  state: () => ({
    tasks: [] as TaskGetSchema[],
  }),
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
