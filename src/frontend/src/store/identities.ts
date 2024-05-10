import { defineStore } from 'pinia'
import { mande } from "mande";

const identities = mande('/api/identities/')

export enum IdentityKind {
  PUBKEY = 'pubkey',
  PASSWORD = "password"
}

export interface IdentityCreateSchema {
  name: string
  kind: IdentityKind
  gecos: string
  homedir: string
  shell: string
  credential: string
}

export interface IdentityGetSchema{
  readonly uid: string
  name: string
  kind: IdentityKind
  gecos: string
  homedir: string
  shell: string
  credential: string
}

export interface IdentityListSchema {
  entries: IdentityGetSchema[]
}

export interface IdentityModifySchema {
  name?: string
  kind?: IdentityKind
  gecos?: string
  homedir?: string
  shell?: string
  credential?: string
}

export const useIdentitiesStore = defineStore('identities', {
  state: () => ({
    identities: [] as IdentityGetSchema[]
  }),
  actions: {
    async list() {
      let identity_list: IdentityListSchema = await identities.get()
      this.identities = identity_list.entries
    },
    async get(uid: string): Promise<IdentityGetSchema> {
      return await identities.get(uid)
    },
    async create(create: IdentityCreateSchema): Promise<IdentityGetSchema> {
      return await identities.post(create)
    },
    async modify(uid: string, modify: IdentityModifySchema): Promise<IdentityGetSchema> {
      return await identities.put(uid, modify)
    },
    async remove(uid: string): Promise<void> {
      return await identities.delete(uid)
    }
  }
})
