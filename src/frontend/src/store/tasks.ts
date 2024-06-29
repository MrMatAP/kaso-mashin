import { defineStore } from "pinia";
import { mande } from "mande";
import { Entity, KasoMashinException, ListableEntity } from "@/base_types";

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

export interface TaskListSchema extends ListableEntity {
  entries: TaskGetSchema[];
}

export class TaskGetSchema extends Entity {
  relation: TaskRelation;
  state: TaskState;
  msg: string;
  percent_complete: number;
  outcome?: string;

  constructor(
    uid: string = "",
    name: string = "",
    relation: TaskRelation = TaskRelation.GENERAL,
    state: TaskState = TaskState.RUNNING,
    msg: string = "",
    percent_complete: number = 0,
    outcome: string = "",
  ) {
    super(uid, name);
    this.relation = relation;
    this.state = state;
    this.msg = msg;
    this.percent_complete = percent_complete;
    this.outcome = outcome;
  }
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
    async list(): Promise<Map<string, TaskGetSchema>> {
      try {
        const task_list = await taskAPI.get<TaskListSchema>();
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
          const cached = this.tasks.get(uid);
          if (cached !== undefined) return cached;
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
