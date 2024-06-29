import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { diskSeed } from "../seeds";
import { BinaryScale, BinarySizedValue, EntityNotFoundException } from "@/base_types";
import { DiskCreateSchema, DiskFormat, DiskModifySchema } from "@/store/disks";

describe("Disk Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached disk", async ({ diskStore }) => {
    const cached = diskSeed.entries[0].name;
    diskSeed.entries[0].name = "updated";
    expect((await diskStore.get(diskSeed.entries[0].uid)).name).toEqual(cached);
  });

  storeTest("can be foreced to update the disk", async ({ diskStore }) => {
    diskSeed.entries[0].name = "updated again";
    expect((await diskStore.get(diskSeed.entries[0].uid, true)).name).toEqual(
      diskSeed.entries[0].name,
    );
    expect(diskStore.disks.size).toBe(diskSeed.entries.length);
  });

  storeTest("can create a disk", async ({ diskStore }) => {
    const currentStoreSize = diskStore.disks.size;
    const create = new DiskCreateSchema(
      "disk",
      new BinarySizedValue(2, BinaryScale.M),
      DiskFormat.VDI,
    );
    const created = await diskStore.create(create);
    expect(created.uid).toBeDefined();
    expect(created.name).toEqual(create.name);
    expect(created.path).toBeDefined();
    expect(created.size).toEqual(create.size);
    expect(created.disk_format).toEqual(create.disk_format);
    expect(diskStore.disks.size).toBe(currentStoreSize + 1);
  });

  storeTest("can modify a disk", async ({ diskStore }) => {
    const currentStoreSize = diskStore.disks.size;
    const create = new DiskCreateSchema(
      "disk",
      new BinarySizedValue(2, BinaryScale.M),
      DiskFormat.VDI,
    );
    const created = await diskStore.create(create);
    created.size = new BinarySizedValue(4, BinaryScale.G);
    const modified = await diskStore.modify(created.uid, new DiskModifySchema(created));
    expect(modified.uid).toBeDefined();
    expect(modified.name).toEqual(created.name);
    expect(modified.path).toEqual(created.path);
    expect(modified.size).toEqual(created.size);
    expect(modified.disk_format).toEqual(created.disk_format);
    expect(diskStore.disks.size).toBe(currentStoreSize + 1);
  });

  storeTest("can remove a disk", async ({ diskStore }) => {
    const currentStoreSize = diskStore.disks.size;
    await diskStore.remove(diskSeed.entries[0].uid);
    expect(diskStore.disks.size).toEqual(currentStoreSize - 1);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ diskStore }) => {
    expect(() => diskStore.get("EntityNotFoundException")).rejects.toThrow(EntityNotFoundException);
  });

  storeTest("correctly reports identityOptions", async ({ diskStore }) => {
    expect(diskStore.diskOptions.length).toBe(diskSeed.entries.length);
  });
});
