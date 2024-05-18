import { defineStore } from "pinia";
import { mande } from "mande";

import { Entity, ModifiableEntity, CreatableEntity } from "@/base_types";

const identities = mande("/api/identities/");

export enum IdentityKind {
  PUBKEY = "pubkey",
  PASSWORD = "password",
}

export interface IdentityListSchema {
  entries: IdentityGetSchema[];
}

export class IdentityGetSchema extends Entity {
  kind: IdentityKind = IdentityKind.PUBKEY;
  gecos: string = "";
  homedir: string = "";
  shell: string = "";
  credential: string = "";
}

export class IdentityCreateSchema extends CreatableEntity {
  kind: IdentityKind = IdentityKind.PUBKEY;
  gecos: string = "";
  homedir: string = "";
  shell: string = "";
  credential: string = "";
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
    identities: [] as IdentityGetSchema[],
  }),
  getters: {
    getIndexByUid: (state) => {
      return (uid: string) => state.identities.findIndex((identity) => identity.uid === uid);
    },
    getIdentityByUid: (state) => {
      return (uid: string) => state.identities.find((identity) => identity.uid === uid);
    }
  },
  actions: {
    async list() {
      let identity_list: IdentityListSchema = await identities.get();
      this.identities = identity_list.entries;
    },
    async get(uid: string): Promise<IdentityGetSchema> {
      return await identities.get(uid);
    },
    async create(create: IdentityCreateSchema): Promise<IdentityGetSchema> {
      return await identities.post(create);
    },
    async modify(
      uid: string,
      modify: IdentityModifySchema,
    ): Promise<IdentityGetSchema> {
      return await identities.put(uid, modify);
    },
    async remove(uid: string): Promise<void> {
      return await identities.delete(uid);
    },
  },
});
