import { defineStore } from 'pinia'
import { mande } from "mande";

const images = mande('/api/images/')
const predefined_images = mande('/api/images/predefined')

export class Image {
  image_id: number
  name: string
  url?: string
  path: string
  min_cpu: number
  min_ram: number
  min_space: number

  constructor(image_id: number, name: string, path: string, min_cpu: number, min_ram: number, min_space: number, url?: string) {
    this.image_id = image_id
    this.name = name
    this.path = path
    this.min_cpu = min_cpu
    this.min_ram = min_ram
    this.min_space = min_space
    this.url = url
  }

  static defaultImage(): Image {
    return new Image(0, '', '', 0, 0, 0)
  }
}

export class ImageCreateSchema {
  name: string
  url: string
  min_cpu?: number
  min_ram?: number
  min_space?: number

  constructor(name: string, url: string, min_cpu?: number, min_ram?: number, min_space?: number) {
    this.name = name
    this.url = url
    this.min_cpu = min_cpu
    this.min_ram = min_ram
    this.min_space = min_space
  }

  static fromImage(image: Image): ImageCreateSchema {
    if(image.url != undefined) {
      return new ImageCreateSchema(image.name, image.url, image.min_cpu, image.min_ram, image.min_space)
    }
    throw new Error('Creating an image requires both name and url')
  }
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
    images: [] as Image[],
    predefined_images: [] as PredefinedImage[]
  }),
  actions: {
    async refresh() {
      this.images = await images.get()
      this.predefined_images = await predefined_images.get()
    },
    async create(image: Image) {
      const new_image = ImageCreateSchema.fromImage(image)
      return images.post(new_image)
    },
    async modify(image: Image) {
      return images.put(image.image_id, image)
    },
    async remove(image: Image) {
      return images.delete(image.image_id)
    }
  }
})
