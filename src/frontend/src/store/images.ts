import { defineStore } from "pinia";
import { mande } from "mande";
import {
  BinarySizedValue,
  CreatableEntity,
  Entity,
  UIEntitySelectOptions,
  ModifiableEntity,
  ListableEntity,
  KasoMashinException,
} from "@/base_types";
import { TaskGetSchema } from "@/store/tasks";

const imageAPI = mande("/api/images/");

export interface ImageListSchema extends ListableEntity<ImageGetSchema> {}

export class ImageGetSchema extends Entity {
  path: string;
  url: string;
  min_vcpu: number;
  min_ram: BinarySizedValue = new BinarySizedValue();
  min_disk: BinarySizedValue = new BinarySizedValue();

  constructor(
    uid: string = "",
    name: string = "",
    path: string = "",
    url: string = "",
    min_vcpu: number = 0,
    min_ram: BinarySizedValue = new BinarySizedValue(),
    min_disk: BinarySizedValue = new BinarySizedValue(),
  ) {
    super(uid, name);
    this.path = path;
    this.url = url;
    this.min_vcpu = min_vcpu;
    this.min_ram = min_ram;
    this.min_disk = min_disk;
  }
}

export class ImageCreateSchema extends CreatableEntity {
  url: string;
  min_vcpu: number;
  min_ram: BinarySizedValue;
  min_disk: BinarySizedValue;

  constructor(
    name: string = "",
    url: string = "",
    min_vcpu: number = 0,
    min_ram: BinarySizedValue = new BinarySizedValue(),
    min_disk: BinarySizedValue = new BinarySizedValue(),
  ) {
    super(name);
    this.url = url;
    this.min_vcpu = min_vcpu;
    this.min_ram = min_ram;
    this.min_disk = min_disk;
  }
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
    images: new Map<string, ImageGetSchema>(),
    pendingImages: new Map<string, ImageCreateSchema>(),
  }),
  getters: {
    imageOptions: (state) =>
      Array.from(state.images.values()).map((i) => new UIEntitySelectOptions(i.uid, i.name)),
  },
  actions: {
    async list(): Promise<Map<string, ImageGetSchema>> {
      try {
        const image_list = await imageAPI.get<ImageListSchema>();
        const update = new Set<ImageGetSchema>(image_list.entries);
        this.$patch((state) => update.forEach((i: ImageGetSchema) => state.images.set(i.uid, i)));
        return this.images;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async get(uid: string, force: boolean = false): Promise<ImageGetSchema> {
      try {
        if (!force) {
          const cached = this.images.get(uid);
          if (cached !== undefined) return cached as ImageGetSchema;
        }
        const image = await imageAPI.get<ImageGetSchema>(uid);
        this.$patch((state) => state.images.set(uid, image));
        return image;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async create(create: ImageCreateSchema): Promise<TaskGetSchema> {
      try {
        const task = await imageAPI.post<TaskGetSchema>(create);
        this.$patch((state) => state.pendingImages.set(task.uid, create));
        return task;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async modify(uid: string, modify: ImageModifySchema): Promise<ImageGetSchema> {
      try {
        const entity = await imageAPI.put<ImageGetSchema>(uid, modify);
        this.$patch((state) => state.images.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await imageAPI.delete(uid);
        this.$patch((state) => state.images.delete(uid));
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
  },
});
