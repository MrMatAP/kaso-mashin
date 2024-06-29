import { defineStore } from "pinia";
import { mande } from "mande";

import {
  Entity,
  ModifiableEntity,
  CreatableEntity,
  ListableEntity,
  UIEntitySelectOptions,
  KasoMashinException,
} from "@/base_types";

const identityAPI = mande("/api/identities/");

export enum IdentityKind {
  PUBKEY = "pubkey",
  PASSWORD = "password",
}

export interface IdentityListSchema extends ListableEntity<IdentityGetSchema> {}

export class IdentityGetSchema extends Entity {
  kind: IdentityKind;
  gecos: string;
  homedir: string;
  shell: string;
  credential: string;

  constructor(
    uid: string = "",
    name: string = "",
    kind: IdentityKind = IdentityKind.PUBKEY,
    gecos: string = "",
    homedir: string = "",
    shell: string = "",
    credential: string = "",
  ) {
    super(uid, name);
    this.kind = kind;
    this.gecos = gecos;
    this.homedir = homedir;
    this.shell = shell;
    this.credential = credential;
  }
}

export class IdentityCreateSchema extends CreatableEntity {
  kind: IdentityKind;
  gecos: string;
  homedir: string;
  shell: string;
  credential: string;

  constructor(
    name: string = "",
    kind: IdentityKind = IdentityKind.PUBKEY,
    gecos: string = "",
    homedir: string = "",
    shell: string = "",
    credential: string = "",
  ) {
    super(name);
    this.kind = kind;
    this.gecos = gecos;
    this.homedir = homedir;
    this.shell = shell;
    this.credential = credential;
  }
}

export class IdentityModifySchema extends ModifiableEntity<IdentityGetSchema> {
  kind: IdentityKind;
  gecos: string;
  homedir: string;
  shell: string;
  credential: string;

  constructor(original: IdentityGetSchema) {
    super(original);
    this.kind = original.kind;
    this.gecos = original.gecos;
    this.homedir = original.homedir;
    this.shell = original.shell;
    this.credential = original.credential;
  }
}

export const useIdentityStore = defineStore("identities", {
  state: () => ({
    identities: new Map<string, IdentityGetSchema>(),
  }),
  getters: {
    identityOptions: (state) =>
      Array.from(state.identities.values()).map((i) => new UIEntitySelectOptions(i.uid, i.name)),
  },
  actions: {
    async list(): Promise<Map<string, IdentityGetSchema>> {
      try {
        const identity_list: IdentityListSchema = await identityAPI.get<IdentityListSchema>();
        const update = new Set<IdentityGetSchema>(identity_list.entries);
        this.$patch((state) => {
          update.forEach((i: IdentityGetSchema) => state.identities.set(i.uid, i));
        });
        return this.identities;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async get(uid: string, force: boolean = false): Promise<IdentityGetSchema> {
      try {
        if (!force) {
          const cached = this.identities.get(uid);
          if (cached !== undefined) return cached as IdentityGetSchema;
        }
        const identity = await identityAPI.get<IdentityGetSchema>(uid);
        this.$patch((state) => state.identities.set(uid, identity));
        return identity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async create(create: IdentityCreateSchema): Promise<IdentityGetSchema> {
      try {
        const entity = await identityAPI.post<IdentityGetSchema>(create);
        this.$patch((state) => state.identities.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async modify(uid: string, modify: IdentityModifySchema): Promise<IdentityGetSchema> {
      try {
        const entity = await identityAPI.put<IdentityGetSchema>(uid, modify);
        this.$patch((state) => state.identities.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await identityAPI.delete(uid);
        this.$patch((state) => state.identities.delete(uid));
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
  },
});
