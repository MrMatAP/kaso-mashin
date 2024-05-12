import { defineStore } from "pinia";
import { mande } from "mande";
import { BinarySizedValue } from "@/base_types";
import { TaskGetSchema } from "@/store/tasks";

const images = mande("/api/images/");

export interface ImageListSchema {
  entries: ImageGetSchema[];
}

export class ImageGetSchema {
  readonly uid: string = "";
  name: string = "";
  path: string = "";
  url: string = "";
  min_vcpu: number = 0;
  min_ram: BinarySizedValue = new BinarySizedValue();
  min_disk: BinarySizedValue = new BinarySizedValue();
}

export class ImageCreateSchema {
  name: string = "";
  url: string = "";
  min_vcpu: number = 0;
  min_ram: BinarySizedValue = new BinarySizedValue();
  min_disk: BinarySizedValue = new BinarySizedValue();
}

export class ImageModifySchema {
  name: string = "";
  min_vcpu: number = 0;
  min_ram: BinarySizedValue = new BinarySizedValue();
  min_disk: BinarySizedValue = new BinarySizedValue();

  constructor(original: ImageGetSchema) {
    this.name = original.name;
    this.min_vcpu = original.min_vcpu;
    this.min_ram = original.min_ram;
    this.min_disk = original.min_disk;
  }
}

export const useImagesStore = defineStore("images", {
  state: () => ({
    images: [] as ImageGetSchema[],
  }),
  actions: {
    async list() {
      let image_list: ImageListSchema = await images.get();
      this.images = image_list.entries;
    },
    async get(uid: string): Promise<ImageGetSchema> {
      return await images.get(uid);
    },
    async create(create: ImageCreateSchema): Promise<TaskGetSchema> {
      return await images.post(create);
    },
    async modify(
      uid: string,
      modify: ImageModifySchema,
    ): Promise<ImageGetSchema> {
      return await images.put(uid, modify);
    },
    async remove(uid: string): Promise<void> {
      return await images.delete(uid);
    },
  },
});
