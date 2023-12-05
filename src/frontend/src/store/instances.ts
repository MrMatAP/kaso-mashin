import { defineStore } from 'pinia'
import { mande } from "mande";
import { Network } from "@/store/networks";

const instances = mande('/api/instances/')

export type Instance = {
  instance_id: number
  name: string
  path: string

  vcpu: number
  ram: number
  mac: string
  display: string
  static_ip4?: string
  bootstrapper: string
  os_disk_path: string
  ci_base_path: string
  vm_script_path: string
  vnc_path: string
  qmp_path: string
  console_path: string
  network: Network
  // image: Image
  // identities: Identity[]
}

export const useInstancesStore = defineStore('instances', {
  state: () => ({
    instances: [] as Instance[]
  }),
  // getters: {
  //   getNetworkById: (state) => {
  //     return (id) => state.networks.find((net) => net.network_id === id)
  // },
  actions: {
    async refresh() {
      this.instances = await instances.get()
    }
  }
})
