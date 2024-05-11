// Utilities
import { defineStore } from "pinia";
import { mande } from "mande";

const networks = mande("/api/networks/");

export enum NetworkKind {
  VMNET_HOST = "vmnet-host",
  VMNET_SHARED = "vmnet-shared",
  VMNET_BRIDGED = "vmnet-bridged",
}

export interface NetworkCreateSchema {
  name: string;
  kind: NetworkKind;
  cidr: string;
  gateway: string;
  dhcp_start: string;
  dhcp_end: string;
}

export interface NetworkGetSchema extends NetworkCreateSchema {
  uid: string;
}

export interface NetworkListSchema {
  entries: NetworkGetSchema[];
}

export interface NetworkModifySchema {
  name?: string;
  cidr?: string;
  gateway?: string;
  dhcp_start?: string;
  dhcp_end?: string;
}

export const useNetworksStore = defineStore("networks", {
  state: () => ({
    networks: [] as NetworkGetSchema[],
  }),
  // getters: {
  //   getNetworkById: (state) => {
  //     return (id) => state.networks.find((net) => net.network_id === id)
  // },
  actions: {
    async list() {
      let network_list: NetworkListSchema = await networks.get();
      this.networks = network_list.entries;
    },
  },
});
