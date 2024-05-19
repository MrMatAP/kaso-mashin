import { defineStore } from "pinia";
import { mande } from "mande";
import {
  BinarySizedValue,
  Entity,
  ModifiableEntity,
  CreatableEntity, EntityNotFoundException, EntityInvariantException
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
    pendingImages: new Map<string, ImageCreateSchema>(),
  }),
  getters: {
    getIndexByUid: (state) => {
      return (uid: string) => state.images.findIndex((image) => image.uid === uid);
    },
    getImageByUid: (state) => {
      return (uid: string) => state.images.find((image) => image.uid === uid);
    }
  },
  actions: {
    async list(): Promise<ImageGetSchema[]> {
      let image_list = await imageAPI.get<ImageListSchema>();
      this.images = image_list.entries;
      return this.images;
    },
    async get(uid: string): Promise<ImageGetSchema> {
      try {
        let image = await imageAPI.get<ImageGetSchema>(uid);
        let index = this.getIndexByUid(uid)
        if(index !== -1) {
          this.images[index] = image
        } else {
          this.images.push(image);
        }
        return image
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg)
      }
    },
    async create(create: ImageCreateSchema): Promise<TaskGetSchema> {
      try {
        let task = await imageAPI.post<TaskGetSchema>(create)
        this.pendingImages.set(task.uid, create)
        return task
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async modify(uid: string, modify: ImageModifySchema): Promise<ImageGetSchema> {
      try {
        let update = await imageAPI.put<ImageGetSchema>(uid, modify);
        let index = this.getIndexByUid(uid)
        this.images[index] = update
        return update
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await imageAPI.delete(uid);
        let index = this.getIndexByUid(uid)
        this.images.splice(index, 1);
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg)
      }
    },
  },
});
