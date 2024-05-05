// Utilities
import { defineStore } from 'pinia'
import { mande } from "mande"

const config = mande("/api/config/")

export interface ConfigSchema {
  version: string
  path: string
  images_path: string
  instances_path: string
  bootstrap_path: string
  default_os_disk_size: string
  default_phone_home_port: string
  default_host_network_dhcp4_start: string
  default_host_network_dhcp4_end: string
  default_shared_network_dhcp4_start: string
  default_shared_network_dhcp4_end: string
  default_host_network_cidr: string
  default_shared_network_cidr: string
  default_server_host: string
  default_server_port: number
  uefi_code_url: string
  uefi_vars_url: string
  butane_path: string
  qemu_aarch64_path: string
  predefined_images: Map<string, string>
}

export const useConfigStore = defineStore('app', {
  state: () => ({
    config: {} as ConfigSchema
  }),
  actions: {
    async get() {
      this.config = await config.get()
    }
  }
})
