import { defineStore } from "pinia";
import { mande } from "mande";
import {
  BinarySizedValue,
  Entity,
  ModifiableEntity,
  CreatableEntity,
} from "@/base_types";
import { TaskGetSchema } from "@/store/tasks";

const imageAPI = mande("/api/images/");

export interface ImageListSchema {
  entries: ImageGetSchema[];
}

export class ImageGetSchema extends Entity {
  path: string = "";
  url: string = "";
  min_vcpu: number = 0;
  min_ram: BinarySizedValue = new BinarySizedValue();
  min_disk: BinarySizedValue = new BinarySizedValue();
}

export class ImageCreateSchema extends CreatableEntity {
  url: string = "";
  min_vcpu: number = 0;
  min_ram: BinarySizedValue = new BinarySizedValue();
  min_disk: BinarySizedValue = new BinarySizedValue();
}

export class ImageModifySchema extends ModifiableEntity<ImageGetSchema> {
  min_vcpu: number;
  min_ram: BinarySizedValue;
  min_disk: BinarySizedValue;

  constructor(original: ImageGetSchema) {
    super(original);
    this.min_vcpu = original.min_vcpu;
    this.min_ram = original.min_ram;
    this.min_disk = original.min_disk;
  }
}

export const useImageStore = defineStore("images", {
  state: () => ({
    images: [] as ImageGetSchema[],
    pendingImages: [] as ImageCreateSchema[],
  }),
  actions: {
    async list(): Promise<ImageGetSchema[]> {
      let image_list: ImageListSchema = await imageAPI.get();
      this.images = image_list.entries;
      return this.images;
    },
    async get(uid: string): Promise<ImageGetSchema> {
      return await imageAPI.get(uid);
    },
    async create(create: ImageCreateSchema): Promise<TaskGetSchema> {
      return await imageAPI.post(create);
    },
    async modify(uid: string, modify: ImageModifySchema): Promise<ImageGetSchema> {
      return await imageAPI.put(uid, modify);
    },
    async remove(uid: string): Promise<void> {
      return await imageAPI.delete(uid);
    },
  },
});
