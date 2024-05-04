import { defineStore } from 'pinia'
import { mande } from "mande";
import {BinarySizedValue} from "@/base_types";

const instances = mande('/api/instances/')

export enum InstanceState {
  STOPPING = "STOPPING",
  STOPPED = "STOPPED",
  STARTING = "STARTING",
  STARTED = "STARTED"
}

export interface InstanceCreateSchema {
  name: string
  vcpu: number
  ram: BinarySizedValue
  os_disk_size: BinarySizedValue
  image_uid: string
  network_uid: string
  bootstrap_uid: string
}

export interface InstanceGetSchema {
  readonly uid: number
  name: string
  path: string
  vcpu: number
  ram: BinarySizedValue
  mac: string
  // os_disk
  // network
  // bootstrap
  bootstrap_file: string
}

export interface InstanceListSchema {
  entries: InstanceGetSchema[]
}

export interface InstanceModifySchema {
  state?: InstanceState
}

export const useInstancesStore = defineStore('instances', {
  state: () => ({
    instances: [] as InstanceGetSchema[]
  }),
  // getters: {
  //   getNetworkById: (state) => {
  //     return (id) => state.networks.find((net) => net.network_id === id)
  // },
  actions: {
    async list() {
      let instance_list: InstanceListSchema = await instances.get()
      this.instances = instance_list.entries
    }
  }
})
