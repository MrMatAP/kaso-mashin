import { defineStore } from 'pinia'
import { mande } from "mande";

const identities = mande('/api/identities/')

export type Identity = {
  identity_id: number
  name: string
  kind: string
  gecos: string
  homedir: string
  shell: string
  passwd?: string
  pubkey?: string
}

export const useIdentitiesStore = defineStore('identities', {
  state: () => ({
    identities: [] as Identity[]
  }),
  actions: {
    async refresh() {
      this.identities = await identities.get()
    }
  }
})
