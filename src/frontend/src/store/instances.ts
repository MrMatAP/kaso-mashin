import { defineStore } from "pinia";
import { mande } from "mande";
import { BinarySizedValue } from "@/base_types";

const instances = mande("/api/instances/");

export enum InstanceState {
  STOPPING = "STOPPING",
  STOPPED = "STOPPED",
  STARTING = "STARTING",
  STARTED = "STARTED",
}

export interface InstanceListSchema {
  entries: InstanceGetSchema[];
}

export class InstanceGetSchema {
  readonly uid: number = "";
  name: string = "";
  path: string = "";
  vcpu: number = 0;
  ram: BinarySizedValue = new BinarySizedValue();
  mac: string = "";
  // os_disk
  // network
  // bootstrap
  bootstrap_file: string = "";
}

export class InstanceCreateSchema {
  name: string = "";
  vcpu: number = 0;
  ram: BinarySizedValue = new BinarySizedValue();
  os_disk_size: BinarySizedValue = new BinarySizedValue();
  image_uid: string = "";
  network_uid: string = "";
  bootstrap_uid: string = "";
}

export class InstanceModifySchema {
  name: string = "";
  state: InstanceState = InstanceState.STOPPED;

  constructor(original: InstanceGetSchema) {
    this.name = original.name;
    this.state = original.state;
  }
}

export const useInstancesStore = defineStore("instances", {
  state: () => ({
    instances: [] as InstanceGetSchema[],
  }),
  actions: {
    async list() {
      let instance_list: InstanceListSchema = await instances.get();
      this.instances = instance_list.entries;
    },
    async get(uid: string): Promise<InstanceGetSchema> {
      return await instances.get(uid);
    },
    async create(create: InstanceCreateSchema): Promise<InstanceCreateSchema> {
      return await instances.post(create);
    },
    async modify(
      uid: string,
      modify: InstanceModifySchema,
    ): Promise<InstanceCreateSchema> {
      return await instances.put(uid, modify);
    },
    async remove(uid: string): Promise<void> {
      return await instances.delete(uid);
    },
  },
});
