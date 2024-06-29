import { defineStore } from "pinia";
import { mande } from "mande";
import {
  Entity,
  ListableEntity,
  CreatableEntity,
  ModifiableEntity,
  UIEntitySelectOptions,
  KasoMashinException,
} from "@/base_types";

const networkAPI = mande("/api/networks/");

export enum NetworkKind {
  VMNET_HOST = "vmnet-host",
  VMNET_SHARED = "vmnet-shared",
  VMNET_BRIDGED = "vmnet-bridged",
}

export interface NetworkListSchema extends ListableEntity<NetworkGetSchema> {}

export class NetworkGetSchema extends Entity {
  kind: NetworkKind;
  cidr: string;
  gateway: string;
  dhcp_start: string;
  dhcp_end: string;

  constructor(
    uid: string = "",
    name: string = "",
    kind: NetworkKind = NetworkKind.VMNET_SHARED,
    cidr: string = "",
    gateway: string = "",
    dhcp_start: string = "",
    dhcp_end: string = "",
  ) {
    super(uid, name);
    this.kind = kind;
    this.cidr = cidr;
    this.gateway = gateway;
    this.dhcp_start = dhcp_start;
    this.dhcp_end = dhcp_end;
  }
}

export class NetworkCreateSchema extends CreatableEntity {
  kind: NetworkKind;
  cidr: string;
  gateway: string;
  dhcp_start: string;
  dhcp_end: string;

  constructor(
    name: string = "",
    kind: NetworkKind = NetworkKind.VMNET_SHARED,
    cidr: string = "",
    gateway: string = "",
    dhcp_start: string = "",
    dhcp_end: string = "",
  ) {
    super(name);
    this.kind = kind;
    this.cidr = cidr;
    this.gateway = gateway;
    this.dhcp_start = dhcp_start;
    this.dhcp_end = dhcp_end;
  }
}

export class NetworkModifySchema extends ModifiableEntity<NetworkGetSchema> {
  kind: NetworkKind;
  cidr: string;
  gateway: string;
  dhcp_start: string;
  dhcp_end: string;

  constructor(original: NetworkGetSchema) {
    super(original);
    this.kind = original.kind;
    this.cidr = original.cidr;
    this.gateway = original.gateway;
    this.dhcp_start = original.dhcp_start;
    this.dhcp_end = original.dhcp_end;
  }
}

export const useNetworkStore = defineStore("networks", {
  state: () => ({
    networks: new Map<string, NetworkGetSchema>(),
  }),
  getters: {
    networkOptions: (state) =>
      Array.from(state.networks.values()).map(
        (network) => new UIEntitySelectOptions(network.uid, network.name),
      ),
  },
  actions: {
    async list(): Promise<Map<string, NetworkGetSchema>> {
      try {
        const network_list = await networkAPI.get<NetworkListSchema>();
        const update = new Set<NetworkGetSchema>(network_list.entries);
        this.$patch((state) => {
          update.forEach((network: NetworkGetSchema) => state.networks.set(network.uid, network));
        });
        return this.networks;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async get(uid: string, force: boolean = false): Promise<NetworkGetSchema> {
      try {
        if (!force) {
          const cached = this.networks.get(uid);
          if (cached !== undefined) return cached as NetworkGetSchema;
        }
        const network = await networkAPI.get<NetworkGetSchema>(uid);
        this.$patch((state) => state.networks.set(uid, network));
        return network;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async create(create: NetworkCreateSchema): Promise<NetworkGetSchema> {
      try {
        const entity = await networkAPI.post<NetworkGetSchema>(create);
        this.$patch((state) => state.networks.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async modify(uid: string, modify: NetworkModifySchema): Promise<NetworkGetSchema> {
      try {
        const entity = await networkAPI.put<NetworkGetSchema>(uid, modify);
        this.$patch((state) => state.networks.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await networkAPI.delete(uid);
        this.$patch((state) => state.networks.delete(uid));
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
  },
});
