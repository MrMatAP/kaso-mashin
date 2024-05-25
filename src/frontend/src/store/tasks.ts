import { defineStore } from "pinia";
import { mande } from "mande";
import { Entity, EntityInvariantException, EntityNotFoundException } from "@/base_types";

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
  outcome?: string = ''
}

export const useTaskStore = defineStore("tasks", {
  state: () => ({
    tasks: [] as TaskGetSchema[],
  }),
  getters: {
    getIndexByUid: (state) => {
      return (uid: string) => state.tasks.findIndex((task) => task.uid === uid);
    },
    getTaskByUid: (state) => {
      return (uid: string) => state.tasks.find((task) => task.uid === uid);
    },
    pendingNumber: (state) =>
      state.tasks.filter((task) => task.state === TaskState.RUNNING).length,
    pendingTasks: (state) : TaskGetSchema[] => state.tasks.filter( (task) => task.state === TaskState.RUNNING),
    failedTasks: (state) : TaskGetSchema[] => state.tasks.filter( (task) => task.state === TaskState.FAILED),
    doneTasks: (state) : TaskGetSchema[] => state.tasks.filter( (task) => task.state === TaskState.DONE),
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
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
    async track(task: TaskGetSchema) {
      try {
        let index = this.tasks.findIndex((task) => task.uid === task.uid);
        if(index !== -1) {
          this.tasks[index] = task
        } else {
          this.tasks.push(task)
        }
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg)
      }
    }
  },
});
