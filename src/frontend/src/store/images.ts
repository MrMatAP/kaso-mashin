import {defineStore} from 'pinia'
import {mande} from "mande";
import {BinarySizedValue} from "@/base_types";

const images = mande('/api/images/')
const predefined_images = mande('/api/images/predefined/')

export interface ImageCreateSchema {
  name: string,
  url: string,
  min_vcpu: number,
  min_ram: BinarySizedValue,
  min_disk: BinarySizedValue
}

export interface ImageGetSchema {
  uid: string,
  path: string,
  name: string,
  url: string,
  min_vcpu: number,
  min_ram: BinarySizedValue,
  min_disk: BinarySizedValue
}

export interface ImageListSchema {
  entries: ImageGetSchema[]
}

export interface ImageModifySchema {
  min_vcpu?: number,
  min_ram?: BinarySizedValue,
  min_disk?: BinarySizedValue,
}


export class PredefinedImage {
  name: string
  url: string

  constructor(name: string, url: string) {
    this.name = name
    this.url = url
  }
}

export const useImagesStore = defineStore('images', {
  state: () => ({
    images: [] as ImageGetSchema[],
    predefined_images: [] as PredefinedImage[]
  }),
  actions: {
    async list() {
      let image_list: ImageListSchema = await images.get()
      this.images = image_list.entries
      //this.predefined_images = await predefined_images.get()
    }
  }
})
