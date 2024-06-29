import { defineStore } from "pinia";
import { mande } from "mande";
import {
  BinaryScale,
  BinarySizedValue,
  CreatableEntity,
  Entity,
  EntityInvariantException,
  EntityNotFoundException,
  KasoMashinException,
  ListableEntity,
  ModifiableEntity,
  UIEntitySelectOptions,
} from "@/base_types";
import { TaskGetSchema, useTaskStore } from "@/store/tasks";

const instanceAPI = mande("/api/instances/");

export enum InstanceState {
  STOPPING = "STOPPING",
  STOPPED = "STOPPED",
  STARTING = "STARTING",
  STARTED = "STARTED",
}

export interface InstanceListSchema extends ListableEntity<InstanceGetSchema> {}

export class InstanceGetSchema extends Entity {
  path: string;
  vcpu: number;
  ram: BinarySizedValue;
  mac: string;
  os_disk_uid: string;
  os_disk_size: BinarySizedValue;
  network_uid: string;
  bootstrap_uid: string;
  bootstrap_file: string;
  state: InstanceState;

  constructor(
    uid: string = "",
    name: string = "",
    path: string = "",
    vcpu: number = 0,
    ram: BinarySizedValue = new BinarySizedValue(),
    mac: string = "",
    os_disk_uid: string = "",
    os_disk_size: BinarySizedValue = new BinarySizedValue(10, BinaryScale.G),
    network_uid: string = "",
    bootstrap_uid: string = "",
    bootstrap_file: string = "",
    state: InstanceState = InstanceState.STOPPED,
  ) {
    super(uid, name);
    this.path = path;
    this.vcpu = vcpu;
    this.ram = ram;
    this.mac = mac;
    this.os_disk_uid = os_disk_uid;
    this.os_disk_size = os_disk_size;
    this.network_uid = network_uid;
    this.bootstrap_uid = bootstrap_uid;
    this.bootstrap_file = bootstrap_file;
    this.state = state;
  }
}

export class InstanceCreateSchema extends CreatableEntity {
  vcpu: number;
  ram: BinarySizedValue;
  os_disk_size: BinarySizedValue;
  image_uid: string;
  network_uid: string;
  bootstrap_uid: string;

  constructor(
    name: string = "",
    vcpu: number = 1,
    ram: BinarySizedValue = new BinarySizedValue(2, BinaryScale.G),
    os_disk_size: BinarySizedValue = new BinarySizedValue(10, BinaryScale.G),
    image_uid: string = "",
    network_uid: string = "",
    bootstrap_uid: string = "",
  ) {
    super(name);
    this.vcpu = vcpu;
    this.ram = ram;
    this.os_disk_size = os_disk_size;
    this.image_uid = image_uid;
    this.network_uid = network_uid;
    this.bootstrap_uid = bootstrap_uid;
  }
}

export class InstanceModifySchema extends ModifiableEntity<InstanceGetSchema> {
  state: InstanceState;
  vcpu: number;
  ram: BinarySizedValue;

  constructor(original: InstanceGetSchema) {
    super(original);
    this.state = original.state;
    this.vcpu = original.vcpu;
    this.ram = original.ram;
  }
}

export const useInstanceStore = defineStore("instances", {
  state: () => ({
    instances: new Map<string, InstanceGetSchema>(),
    pendingInstances: new Map<string, InstanceCreateSchema>(),
  }),
  getters: {
    instanceOptions: (state) =>
      Array.from(state.instances.values()).map((i) => new UIEntitySelectOptions(i.uid, i.name)),
  },
  actions: {
    async list() {
      try {
        const instance_list = await instanceAPI.get<InstanceListSchema>();
        const update = new Set<InstanceGetSchema>(instance_list.entries);
        this.$patch((state) =>
          update.forEach((i: InstanceGetSchema) => state.instances.set(i.uid, i)),
        );
        return this.instances;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async get(uid: string, force: boolean = false): Promise<InstanceGetSchema> {
      try {
        if (!force) {
          const cached = this.instances.get(uid);
          if (cached) return cached as InstanceGetSchema;
        }
        const instance = await instanceAPI.get<InstanceGetSchema>(uid);
        this.$patch((state) => state.instances.set(uid, instance));
        return instance;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async create(create: InstanceCreateSchema): Promise<TaskGetSchema> {
      try {
        const task = await instanceAPI.post<TaskGetSchema>(create);
        this.$patch((state) => state.pendingInstances.set(task.uid, create));
        return task;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async modify(uid: string, modify: InstanceModifySchema): Promise<InstanceGetSchema> {
      try {
        const entity = await instanceAPI.put<InstanceGetSchema>(uid, modify);
        this.$patch((state) => state.instances.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await instanceAPI.delete(uid);
        this.$patch((state) => state.instances.delete(uid));
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
  },
});
