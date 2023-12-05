// Utilities
import { defineStore } from 'pinia'
import { mande } from "mande";

const networks = mande('/api/networks/')

export type Network = {
  name: string
  kind: string
  network_id: number
  host_if?: string
  host_ip4?: string
  nm4: string
  gw4?: string
  ns4?: string
  dhcp4_start?: string
  dhcp4_end?: string
  host_phone_home_port: number
}

export const useNetworksStore = defineStore('networks', {
  state: () => ({
    networks: [] as Network[]
  }),
  // getters: {
  //   getNetworkById: (state) => {
  //     return (id) => state.networks.find((net) => net.network_id === id)
  // },
  actions: {
    async refresh() {
      this.networks = await networks.get()
    }
  }
})
