import { defineStore } from "pinia";
import { mande } from "mande";
import {
  Entity,
  ModifiableEntity,
  CreatableEntity,
  EntityNotFoundException,
  EntityInvariantException
} from "@/base_types";

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
  getters: {
    getIndexByUid: (state) => {
      return (uid: string) => state.networks.findIndex((network) => network.uid === uid);
    },
    getNetworkByUid: (state) => {
      return (uid: string) => state.networks.find((network) => network.uid === uid);
    }
  },
  actions: {
    async list(): Promise<NetworkGetSchema[]> {
      let network_list = await networkAPI.get<NetworkListSchema>();
      this.networks = network_list.entries;
      return this.networks;
    },
    async get(uid: string): Promise<NetworkGetSchema> {
      try {
        let network = await networkAPI.get<NetworkGetSchema>(uid);
        let index = this.getIndexByUid(uid);
        if(index !== -1) {
          this.networks[index] = network
        } else {
          this.networks.push(network)
        }
        return network
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg)
      }
    },
    async create(create: NetworkCreateSchema): Promise<NetworkGetSchema> {
      try {
        return await networkAPI.post<NetworkGetSchema>(create);
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async modify(
      uid: string,
      modify: NetworkModifySchema,
    ): Promise<NetworkGetSchema> {
      try {
        let update = await networkAPI.put<NetworkGetSchema>(uid, modify);
        let index = this.getIndexByUid(uid);
        this.networks[index] = update
        return update
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg)
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await networkAPI.delete(uid);
        let index = this.getIndexByUid(uid);
        this.networks.splice(index, 1);
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
  },
});
