import { defineStore } from "pinia";
import { mande } from "mande";

import {
  Entity,
  ModifiableEntity,
  CreatableEntity,
  EntityNotFoundException,
  EntityInvariantException
} from "@/base_types";

const identityAPI = mande("/api/identities/");

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
      let identity_list: IdentityListSchema = await identityAPI.get();
      this.identities = identity_list.entries;
      return this.identities;
    },
    async get(uid: string): Promise<IdentityGetSchema> {
      try {
        let identity = await identityAPI.get<IdentityGetSchema>(uid);
        let index = this.getIndexByUid(uid);
        if(index !== -1) {
          this.identities[index] = identity
        } else {
          this.identities.push(identity)
        }
        return identity
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
    async create(create: IdentityCreateSchema): Promise<IdentityGetSchema> {
      try {
        return await identityAPI.post<IdentityGetSchema>(create);
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async modify(
      uid: string,
      modify: IdentityModifySchema,
    ): Promise<IdentityGetSchema> {
      try {
        let update = await identityAPI.put<IdentityGetSchema>(uid, modify);
        let index = this.getIndexByUid(uid);
        this.identities[index] = update;
        return update;
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await identityAPI.delete(uid);
        let index = this.getIndexByUid(uid);
        this.identities.splice(index, 1);
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
  },
});
