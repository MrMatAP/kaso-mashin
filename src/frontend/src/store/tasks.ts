import { defineStore } from "pinia";
import { mande } from "mande";
import {
  Entity,
  EntityInvariantException,
  EntityNotFoundException,
  ExceptionKind,
  KasoMashinException,
} from "@/base_types";

const taskAPI = mande("/api/tasks/");

export enum TaskState {
  RUNNING = "running",
  DONE = "done",
  FAILED = "failed",
}

export enum TaskRelation {
  BOOTSTRAPS = "bootstraps",
  DISKS = "disks",
  IDENTITIES = "identities",
  IMAGES = "images",
  INSTANCES = "instances",
  NETWORKS = "networks",
  GENERAL = "general",
}

export interface TaskListSchema {
  entries: TaskGetSchema[];
}

export class TaskGetSchema extends Entity {
  relation: TaskRelation = TaskRelation.GENERAL;
  state: TaskState = TaskState.RUNNING;
  msg: string = "";
  percent_complete: number = 0;
  outcome?: string = "";
}

export const useTaskStore = defineStore("tasks", {
  state: () => ({
    tasks: new Map<string, TaskGetSchema>(),
  }),
  getters: {
    allTasks: (state): TaskGetSchema[] => Array.from(state.tasks.values()),
    runningTasks: (state): TaskGetSchema[] =>
      Array.from(state.tasks.values()).filter((task) => task.state === TaskState.RUNNING),
    failedTasks: (state): TaskGetSchema[] =>
      Array.from(state.tasks.values()).filter((task) => task.state === TaskState.FAILED),
    doneTasks: (state): TaskGetSchema[] =>
      Array.from(state.tasks.values()).filter((task) => task.state === TaskState.DONE),
  },
  actions: {
    async list() {
      try {
        const task_list: TaskListSchema = await taskAPI.get();
        const update = new Set<TaskGetSchema>(task_list.entries);
        this.$patch((state) => {
          update.forEach((task) => state.tasks.set(task.uid, task));
        });
        return this.tasks;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async get(uid: string, force: boolean = false): Promise<TaskGetSchema> {
      try {
        if (!force) {
          const cached_task = this.tasks.get(uid);
          if (cached_task !== undefined) return cached_task;
        }
        const task = await taskAPI.get<TaskGetSchema>(uid);
        this.$patch((state) => state.tasks.set(uid, task));
        return task;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
  },
});
