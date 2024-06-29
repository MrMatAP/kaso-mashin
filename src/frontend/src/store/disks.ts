import { defineStore } from "pinia";
import { mande } from "mande";
import {
  Entity,
  ModifiableEntity,
  CreatableEntity,
  BinarySizedValue,
  KasoMashinException,
  ListableEntity,
  UIEntitySelectOptions,
} from "@/base_types";

const diskAPI = mande("/api/disks/");

export enum DiskFormat {
  Raw = "raw",
  QCow2 = "qcow2",
  VDI = "vdi",
}

export interface DiskListSchema extends ListableEntity<DiskGetSchema> {}

export class DiskGetSchema extends Entity {
  path;
  size: BinarySizedValue;
  disk_format;
  image_uid;

  constructor(
    uid: string = "",
    name: string = "",
    path: string = "",
    size: BinarySizedValue = new BinarySizedValue(),
    disk_format: DiskFormat = DiskFormat.QCow2,
    image_uid: string = "",
  ) {
    super(uid, name);
    this.path = path;
    this.size = size;
    this.disk_format = disk_format;
    this.image_uid = image_uid;
  }
}

export class DiskCreateSchema extends CreatableEntity {
  size: BinarySizedValue;
  disk_format: DiskFormat;
  image_uid?: string;

  constructor(
    name: string = "",
    size: BinarySizedValue = new BinarySizedValue(),
    disk_format: DiskFormat = DiskFormat.QCow2,
    image_uid: string = "",
  ) {
    super(name);
    this.size = size;
    this.disk_format = disk_format;
    this.image_uid = image_uid;
  }
}

export class DiskModifySchema extends ModifiableEntity<DiskGetSchema> {
  size: BinarySizedValue = new BinarySizedValue();

  constructor(original: DiskGetSchema) {
    super(original);
    this.size = original.size;
  }
}

export const useDiskStore = defineStore("disks", {
  state: () => ({
    disks: new Map<string, DiskGetSchema>(),
  }),
  getters: {
    diskOptions: (state) =>
      Array.from(state.disks.values()).map((i) => new UIEntitySelectOptions(i.uid, i.name)),
  },
  actions: {
    async list() {
      try {
        const disk_list = await diskAPI.get<DiskListSchema>();
        const update = new Set<DiskGetSchema>(disk_list.entries);
        this.$patch((state) => update.forEach((d) => state.disks.set(d.uid, d)));
        return this.disks;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async get(uid: string, force: boolean = false): Promise<DiskGetSchema> {
      try {
        if (!force) {
          const cached = this.disks.get(uid);
          if (cached) return cached as DiskGetSchema;
        }
        const disk = await diskAPI.get<DiskGetSchema>(uid);
        this.$patch((state) => state.disks.set(uid, disk));
        return disk;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async create(create: DiskCreateSchema): Promise<DiskGetSchema> {
      try {
        const entity = await diskAPI.post<DiskGetSchema>(create);
        this.$patch((state) => state.disks.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async modify(uid: string, modify: DiskModifySchema): Promise<DiskGetSchema> {
      try {
        const entity = await diskAPI.put<DiskGetSchema>(uid, modify);
        this.$patch((state) => state.disks.set(entity.uid, entity));
        return entity;
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await diskAPI.delete(uid);
        this.$patch((state) => state.disks.delete(uid));
      } catch (error: any) {
        throw KasoMashinException.fromError(error);
      }
    },
  },
});
