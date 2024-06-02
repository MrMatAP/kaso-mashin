import { defineStore } from "pinia";
import { mande } from "mande";
import {
  CreatableEntity,
  Entity,
  EntityInvariantException,
  EntityNotFoundException,
  UIEntitySelectOptions,
  ModifiableEntity,
} from "@/base_types";

const bootstrapAPI = mande("/api/bootstraps/");

export enum BootstrapKind {
  IGNITION = "ignition",
  CLOUD_INIT = "cloud-init",
}

export interface BootstrapListSchema {
  entries: BootstrapGetSchema[];
}

export class BootstrapGetSchema extends Entity {
  kind: BootstrapKind = BootstrapKind.IGNITION;
  content: string = "";
  required_keys: Array<string> = [];
}

export class BootstrapCreateSchema extends CreatableEntity {
  kind: BootstrapKind = BootstrapKind.IGNITION;
  content: string = "";
}

export class BootstrapModifySchema extends ModifiableEntity<BootstrapGetSchema> {
  kind: BootstrapKind = BootstrapKind.IGNITION;
  content: string = "";

  constructor(original: BootstrapGetSchema) {
    super(original);
    this.kind = original.kind;
    this.content = original.content;
  }
}

export const useBootstrapStore = defineStore("bootstraps", {
  state: () => ({
    bootstraps: [] as BootstrapGetSchema[],
  }),
  getters: {
    getIndexByUid: (state) => {
      return (uid: string) => state.bootstraps.findIndex((bootstrap) => bootstrap.uid === uid);
    },
    getBootstrapByUid: (state) => {
      return (uid: string) => state.bootstraps.find((bootstrap) => bootstrap.uid === uid);
    },
    bootstrapOptions: (state) =>
      state.bootstraps.map((bootstrap) => new UIEntitySelectOptions(bootstrap.uid, bootstrap.name)),
  },
  actions: {
    async list(): Promise<BootstrapGetSchema[]> {
      const bootstrap_list = await bootstrapAPI.get<BootstrapListSchema>();
      this.bootstraps = bootstrap_list.entries;
      return this.bootstraps;
    },
    async get(uid: string): Promise<BootstrapGetSchema> {
      try {
        const bootstrap = await bootstrapAPI.get<BootstrapGetSchema>(uid);
        const index = this.getIndexByUid(uid);
        if (index !== -1) {
          this.bootstraps[index] = bootstrap;
        } else {
          this.bootstraps.push(bootstrap);
        }
        return bootstrap;
      } catch (error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
    async create(create: BootstrapCreateSchema): Promise<BootstrapGetSchema> {
      try {
        return await bootstrapAPI.post<BootstrapGetSchema>(create);
      } catch (error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async modify(uid: string, modify: BootstrapModifySchema): Promise<BootstrapGetSchema> {
      try {
        const update = await bootstrapAPI.put<BootstrapGetSchema>(uid, modify);
        const index = this.getIndexByUid(uid);
        this.bootstraps[index] = update;
        return update;
      } catch (error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await bootstrapAPI.delete(uid);
        const index = this.getIndexByUid(uid);
        this.bootstraps.splice(index, 1);
      } catch (error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
  },
});
