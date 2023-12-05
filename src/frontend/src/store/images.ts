import { defineStore } from 'pinia'
import { mande } from "mande";

const images = mande('/api/images/')

export type Image = {
  image_id: number
  name: string
  path: string
  min_cpu: number
  min_ram: number
  min_space: number
}

export const useImagesStore = defineStore('images', {
  state: () => ({
    images: [] as Image[]
  }),
  actions: {
    async refresh() {
      this.images = await images.get()
    }
  }
})
