import { defineStore } from 'pinia'
import { mande } from "mande";

const identities = mande('/api/identities/')

export enum IdentityKind {
  pubkey = 'pubkey',
  password = "password"
}

export class Identity {
  identity_id: number
  name: string
  kind: IdentityKind
  gecos: string
  homedir: string
  shell: string
  passwd?: string
  pubkey?: string

  constructor(identity_id: number, name: string, kind: IdentityKind, gecos: string, homedir: string, shell: string, passwd?: string, pubkey?: string) {
    this.identity_id = identity_id
    this.name = name
    this.kind = kind
    this.gecos = gecos
    this.homedir = homedir
    this.shell = shell
    this.passwd = passwd
    this.pubkey = pubkey
  }

  static defaultIdentity(): Identity {
    return new Identity(0, '', IdentityKind.pubkey, '', '', '/bin/bash', '', '')
  }

  static displayKind(kind: IdentityKind): string {
    switch(kind) {
      case IdentityKind.password: return 'Password'
      case IdentityKind.pubkey: return 'SSH Public Key'
      default: return 'Unknown'
    }
  }
}

export const useIdentitiesStore = defineStore('identities', {
  state: () => ({
    identities: [] as Identity[]
  }),
  actions: {
    async refresh() {
      this.identities = await identities.get()
    },
    async create(identity: Identity) {
      return identities.post(identity)
    },
    async modify(identity: Identity) {
      return identities.put(identity.identity_id, identity)
    },
    async remove(identity: Identity) {
      return identities.delete(identity.identity_id)
    }
  }
})
