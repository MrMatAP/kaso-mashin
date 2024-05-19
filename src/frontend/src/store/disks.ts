import { defineStore } from 'pinia';
import { mande } from 'mande';
import {
  Entity,
  ModifiableEntity,
  CreatableEntity,
  EntityNotFoundException,
  EntityInvariantException,
  BinarySizedValue
} from "@/base_types";

const diskAPI = mande('/api/disks/');

export enum DiskFormat {
  Raw = "raw",
  QCow2 = "qcow2",
  VDI = "vdi"
}

export interface DiskListSchema {
  entries: DiskGetSchema[];
}

export class DiskGetSchema extends Entity {
  path: string = "";
  size: BinarySizedValue = new BinarySizedValue();
  disk_format: DiskFormat = DiskFormat.QCow2;
  image_uid: string = "";
}

export class DiskCreateSchema extends CreatableEntity {
  size: BinarySizedValue = new BinarySizedValue();
  disk_format: DiskFormat = DiskFormat.QCow2;
  image_uid?: string = "";
}

export class DiskModifySchema extends ModifiableEntity<DiskGetSchema> {
  size: BinarySizedValue = new BinarySizedValue();

  constructor(original: DiskGetSchema) {
    super(original);
    this.size = original.size;
  }
}

export const useDiskStore = defineStore('disks', {
  state: () => ({
    disks: [] as DiskGetSchema[],
  }),
  getters: {
    getIndexByUid: (state) => {
      return (uid: string) => state.disks.findIndex((disk) => disk.uid === uid);
    },
    getInstanceByUid: (state) => {
      return (uid: string) => state.disks.find((disk) => disk.uid === uid);
    },
  },
  actions: {
    async list() {
      let disk_list = await diskAPI.get<DiskListSchema>();
      this.disks = disk_list.entries;
      return this.disks;
    },
    async get(uid: string): Promise<DiskGetSchema> {
      try {
        let instance = await diskAPI.get<DiskGetSchema>(uid);
        let index = this.getIndexByUid(uid);
        if(index !== -1) {
          this.disks[index] = instance
        } else {
          this.disks.push(instance)
        }
        return instance;
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg)
      }
    },
    async create(create: DiskCreateSchema): Promise<DiskGetSchema> {
      try {
        let disk = await diskAPI.post<DiskGetSchema>(create);
        this.disks.push(disk)
        return disk;
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg);
      }
    },
    async modify(
      uid: string,
      modify: DiskModifySchema,
    ): Promise<DiskGetSchema> {
      try {
        let update = await diskAPI.put<DiskGetSchema>(uid, modify);
        let index = this.getIndexByUid(uid);
        this.disks[index] = update
        return update
      } catch(error: any) {
        throw new EntityInvariantException(error.body.status, error.body.msg)
      }
    },
    async remove(uid: string): Promise<void> {
      try {
        await diskAPI.delete(uid);
        let index = this.getIndexByUid(uid);
        this.disks.splice(index, 1);
      } catch(error: any) {
        throw new EntityNotFoundException(error.body.status, error.body.msg);
      }
    },
  }
})
