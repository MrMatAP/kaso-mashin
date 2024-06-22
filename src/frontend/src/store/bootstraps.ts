import { defineStore } from "pinia";
import { mande } from "mande";
import {
  CreatableEntity,
  Entity,
  UIEntitySelectOptions,
  ModifiableEntity,
  KasoMashinException,
  ListableEntity,
} from "@/base_types";

const bootstrapAPI = mande("/api/bootstraps/");

export enum BootstrapKind {
  IGNITION = "ignition",
  CLOUD_INIT = "cloud-init",
}

export interface BootstrapListSchema extends ListableEntity {
  entries: BootstrapGetSchema[];
}

export class BootstrapGetSchema extends Entity {
  kind: BootstrapKind;
  content: string;
  required_keys: Array<string>;

  constructor(
    uid: string,
    name: string = "",
    kind: BootstrapKind = BootstrapKind.IGNITION,
    content: string = "",
    required_keys: Array<string> = [],
  ) {
    super(uid, name);
    this.kind = kind;
    this.content = content;
    this.required_keys = required_keys;
  }
}

export class BootstrapCreateSchema extends CreatableEntity {
  kind: BootstrapKind;
  content: string;

  constructor(name: string, kind: BootstrapKind = BootstrapKind.IGNITION, content: string) {
    super(name);
    this.kind = kind;
    this.content = content;
  }
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
    bootstraps: new Map<string, BootstrapGetSchema>(),
  }),
  getters: {
    bootstrapOptions: (state): UIEntitySelectOptions[] =>
      Array.from(state.bootstraps.values()).map(
        (bootstrap) => new UIEntitySelectOptions(bootstrap.uid, bootstrap.name),
      ),
  },
  actions: {
    async list(): Promise<Map<string, BootstrapGetSchema>> {
      const bootstrap_list = await bootstrapAPI.get<BootstrapListSchema>();
      const update = new Set<BootstrapGetSchema>(bootstrap_list.entries);
      this.$patch((state) => {
        update.forEach((bootstrap: BootstrapGetSchema) =>
          state.bootstraps.set(bootstrap.uid, bootstrap),
        );
      });
      return this.bootstraps;
    },
    async get(uid: string, force: boolean = false): Promise<BootstrapGetSchema> {
      try {
        if (!force) {
          const cached = this.bootstraps.get(uid);
          if (cached !== undefined) return cached;
        }
        const bootstrap = await bootstrapAPI.get<BootstrapGetSchema>(uid);
        this.$patch((state) => state.bootstraps.set(uid, bootstrap));
        return bootstrap;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async create(create: BootstrapCreateSchema): Promise<BootstrapGetSchema> {
      try {
        const entity = await bootstrapAPI.post<BootstrapGetSchema>(create);
        this.$patch((state) => state.bootstraps.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async modify(uid: string, modify: BootstrapModifySchema): Promise<BootstrapGetSchema> {
      try {
        const entity = await bootstrapAPI.put<BootstrapGetSchema>(uid, modify);
        this.$patch((state) => state.bootstraps.set(uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await bootstrapAPI.delete(uid);
        this.$patch((state) => {
          state.bootstraps.delete(uid);
        });
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
  },
});
