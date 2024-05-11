// Utilities
import { defineStore } from "pinia";
import { mande } from "mande";

const networks = mande("/api/networks/");

export enum NetworkKind {
  VMNET_HOST = "vmnet-host",
  VMNET_SHARED = "vmnet-shared",
  VMNET_BRIDGED = "vmnet-bridged",
}

export interface NetworkListSchema {
  entries: NetworkGetSchema[];
}

export class NetworkGetSchema {
  readonly uid: string = "";
  name: string = "";
  kind: NetworkKind = NetworkKind.VMNET_SHARED;
  cidr: string = '';
  gateway: string = '';
  dhcp_start: string = '';
  dhcp_end: string = '';
}

export class NetworkCreateSchema {
  name: string = '';
  kind: NetworkKind = NetworkKind.VMNET_SHARED;
  cidr: string = '';
  gateway: string = '';
  dhcp_start: string = '';
  dhcp_end: string = '';
}

export class NetworkModifySchema {
  name: string;
  cidr: string;
  gateway: string;
  dhcp_start: string;
  dhcp_end: string;

  constructor(original: NetworkGetSchema) {
    this.name = original.name;
    this.cidr = original.cidr;
    this.gateway = original.gateway;
    this.dhcp_start = original.dhcp_start;
    this.dhcp_end = original.dhcp_end;
  }
}

export const useNetworksStore = defineStore("networks", {
  state: () => ({
    networks: [] as NetworkGetSchema[],
  }),
  actions: {
    async list() {
      let network_list: NetworkListSchema = await networks.get();
      this.networks = network_list.entries;
    },
    async get(uid: string): Promise<NetworkGetSchema> {
      return await networks.get(uid);
    },
    async create(create: NetworkCreateSchema): Promise<NetworkGetSchema> {
      return await networks.post(create);
    },
    async modify(uid: string, modify: NetworkModifySchema): Promise<NetworkGetSchema> {
      return await networks.put(uid, modify);
    },
    async remove(uid: string): Promise<void> {
      return await networks.delete(uid);
    }
  },
});
