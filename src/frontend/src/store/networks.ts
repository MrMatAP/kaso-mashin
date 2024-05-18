import { defineStore } from "pinia";
import { mande } from "mande";
import { Entity, ModifiableEntity, CreatableEntity } from "@/base_types";

const networkAPI = mande("/api/networks/");

export enum NetworkKind {
  VMNET_HOST = "vmnet-host",
  VMNET_SHARED = "vmnet-shared",
  VMNET_BRIDGED = "vmnet-bridged",
}

export interface NetworkListSchema {
  entries: NetworkGetSchema[];
}

export class NetworkGetSchema extends Entity {
  kind: NetworkKind = NetworkKind.VMNET_SHARED;
  cidr: string = "";
  gateway: string = "";
  dhcp_start: string = "";
  dhcp_end: string = "";
}

export class NetworkCreateSchema extends CreatableEntity {
  kind: NetworkKind = NetworkKind.VMNET_SHARED;
  cidr: string = "";
  gateway: string = "";
  dhcp_start: string = "";
  dhcp_end: string = "";
}

export class NetworkModifySchema extends ModifiableEntity<NetworkGetSchema> {
  cidr: string;
  gateway: string;
  dhcp_start: string;
  dhcp_end: string;

  constructor(original: NetworkGetSchema) {
    super(original);
    this.cidr = original.cidr;
    this.gateway = original.gateway;
    this.dhcp_start = original.dhcp_start;
    this.dhcp_end = original.dhcp_end;
  }
}

export const useNetworkStore = defineStore("networks", {
  state: () => ({
    networks: [] as NetworkGetSchema[],
  }),
  actions: {
    async list(): Promise<NetworkGetSchema[]> {
      let network_list: NetworkListSchema = await networkAPI.get();
      this.networks = network_list.entries;
      return this.networks;
    },
    async get(uid: string): Promise<NetworkGetSchema> {
      return await networkAPI.get(uid);
    },
    async create(create: NetworkCreateSchema): Promise<NetworkGetSchema> {
      return await networkAPI.post(create);
    },
    async modify(
      uid: string,
      modify: NetworkModifySchema,
    ): Promise<NetworkGetSchema> {
      return await networkAPI.put(uid, modify);
    },
    async remove(uid: string): Promise<void> {
      return await networkAPI.delete(uid);
    },
  },
});
