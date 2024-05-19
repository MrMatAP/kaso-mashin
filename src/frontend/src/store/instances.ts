import { defineStore } from "pinia";
import { mande } from "mande";
import {
  BinarySizedValue,
  Entity,
  ModifiableEntity,
  CreatableEntity, EntityNotFoundException, EntityInvariantException
} from "@/base_types";
import { TaskGetSchema, TaskState } from "@/store/tasks";
import { NetworkGetSchema } from "@/store/networks";

const instanceAPI = mande("/api/instances/");

export enum InstanceState {
  STOPPING = "STOPPING",
  STOPPED = "STOPPED",
  STARTING = "STARTING",
  STARTED = "STARTED",
}

export interface InstanceListSchema {
  entries: InstanceGetSchema[];
}

export class InstanceGetSchema extends Entity {
  path: string = "";
  state: InstanceState = InstanceState.STOPPED;
  vcpu: number = 0;
  ram: BinarySizedValue = new BinarySizedValue();
  mac: string = "";
  // os_disk
  network: NetworkGetSchema = new NetworkGetSchema();
  // bootstrap
  bootstrap_file: string = "";
}

export class InstanceCreateSchema extends CreatableEntity {
  vcpu: number = 0;
  ram: BinarySizedValue = new BinarySizedValue();
  os_disk_size: BinarySizedValue = new BinarySizedValue();
  image_uid: string = "";
  network_uid: string = "";
  bootstrap_uid: string = "";
}

export class InstanceModifySchema extends ModifiableEntity<InstanceGetSchema> {
  state: InstanceState = InstanceState.STOPPED;
  vcpu: number = 0;
  ram: BinarySizedValue = new BinarySizedValue();

  constructor(original: InstanceGetSchema) {
    super(original);
    this.state = original.state;
    this.vcpu = original.vcpu;
    this.ram = original.ram;
  }
}

export const useInstanceStore = defineStore("instances", {
  state: () => ({
    instances: [] as InstanceGetSchema[],
    pendingInstances: new Map<string, InstanceCreateSchema>(),
  }),
  getters: {
    getIndexByUid: (state) => {
      return (uid: string) => state.instances.findIndex((instance) => instance.uid === uid);
    },
    getInstanceByUid: (state) => {
      return (uid: string) => state.instances.find((instance) => instance.uid === uid);
    },
  },
  actions: {
    async list() {
      let instance_list: InstanceListSchema = await instanceAPI.get();
      this.instances = instance_list.entries;
      return this.instances;
    },
    async get(uid: string): Promise<InstanceGetSchema> {
      try {
        let instance = await instanceAPI.get<InstanceGetSchema>(uid);
        let index = this.getIndexByUid(uid);
        if(index !== -1) {
          this.instances[index] = instance
        } else {
          this.instances.push(instance)
        }
        return instance;
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg)
      }
    },
    async create(create: InstanceCreateSchema): Promise<TaskGetSchema> {
      try {
        let task = await instanceAPI.post<TaskGetSchema>(create);
        this.pendingInstances.set(task.uid, create);
        return task;
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async modify(
      uid: string,
      modify: InstanceModifySchema,
    ): Promise<InstanceGetSchema> {
      try {
        let update = await instanceAPI.put<InstanceGetSchema>(uid, modify);
        let index = this.getIndexByUid(uid);
        this.instances[index] = update
        return update
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg)
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await instanceAPI.delete(uid);
        let index = this.getIndexByUid(uid);
        this.instances.splice(index, 1);
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
  },
});
