import { defineStore } from "pinia";
import { mande } from "mande";
import { Entity, EntityNotFoundExceptionSchema, ExceptionSchema } from "@/base_types";

const taskAPI = mande("/api/tasks/");

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

export const useTaskStore = defineStore("tasks", {
  state: () => ({
    tasks: [] as TaskGetSchema[],
  }),
  getters: {
    pendingNumber: (state) =>
      state.tasks.filter((task) => task.state === TaskState.RUNNING).length,
    pendingTasks: (state) : TaskGetSchema[] => state.tasks.filter( (task) => task.state === TaskState.RUNNING),
  },
  actions: {
    async list() {
      let task_list: TaskListSchema = await taskAPI.get();
      this.tasks = task_list.entries;
      return this.tasks;
    },
    async get(uid: string): Promise<TaskGetSchema> {
      try {
        let task = await taskAPI.get<TaskGetSchema>(uid);
        let index = this.tasks.findIndex((task) => task.uid === uid);
        if(index !== -1) {
          this.tasks[index] = task
        } else {
          this.tasks.push(task)
        }
        return task;
      } catch (error: any) {
        throw new EntityNotFoundExceptionSchema(error.body.status, error.body.msg);
      }
    },
  },
});
