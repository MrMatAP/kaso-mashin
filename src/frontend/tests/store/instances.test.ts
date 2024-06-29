import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { instanceSeed } from "../seeds";
import { BinaryScale, BinarySizedValue, EntityNotFoundException } from "@/base_types";
import { InstanceCreateSchema, InstanceModifySchema } from "@/store/instances";

describe("instance Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached instance", async ({ instanceStore }) => {
    const cached = instanceSeed.entries[0].name;
    instanceSeed.entries[0].name = "updated";
    expect((await instanceStore.get(instanceSeed.entries[0].uid)).name).toEqual(cached);
  });

  storeTest("can be foreced to update the instance", async ({ instanceStore }) => {
    instanceSeed.entries[0].name = "updated again";
    expect((await instanceStore.get(instanceSeed.entries[0].uid, true)).name).toEqual(
      instanceSeed.entries[0].name,
    );
    expect(instanceStore.instances.size).toBe(instanceSeed.entries.length);
  });

  storeTest("can create an instance", async ({ instanceStore }) => {
    const currentStoreSize = instanceStore.instances.size;
    const currentPendingSize = instanceStore.pendingInstances.size;
    const create = new InstanceCreateSchema(
      "Test instance",
      2,
      new BinarySizedValue(2, BinaryScale.M),
      new BinarySizedValue(2, BinaryScale.M),
      crypto.randomUUID(),
      crypto.randomUUID(),
      crypto.randomUUID(),
    );
    const created = await instanceStore.create(create);
    expect(created.uid).toBeDefined();
    expect(instanceStore.instances.size).toBe(currentStoreSize);
    expect(instanceStore.pendingInstances.size).toBe(currentPendingSize + 1);
  });

  storeTest("can modify an instance", async ({ instanceStore }) => {
    const currentStoreSize = instanceStore.instances.size;
    instanceSeed.entries[0].name = "Modified";
    const modified = await instanceStore.modify(
      instanceSeed.entries[0].uid,
      new InstanceModifySchema(instanceSeed.entries[0]),
    );
    expect(modified.uid).toBeDefined();
    expect(modified.name).toEqual(instanceSeed.entries[0].name);
    expect(modified.path).toEqual(instanceSeed.entries[0].path);
    expect(modified.vcpu).toEqual(instanceSeed.entries[0].vcpu);
    expect(modified.ram).toEqual(instanceSeed.entries[0].ram);
    expect(modified.os_disk_uid).toEqual(instanceSeed.entries[0].os_disk_uid);
    expect(modified.os_disk_size).toEqual(instanceSeed.entries[0].os_disk_size);
    expect(modified.network_uid).toEqual(instanceSeed.entries[0].network_uid);
    expect(modified.bootstrap_uid).toEqual(instanceSeed.entries[0].bootstrap_uid);
    expect(modified.bootstrap_file).toEqual(instanceSeed.entries[0].bootstrap_file);
    expect(modified.state).toEqual(instanceSeed.entries[0].state);
    expect(instanceStore.instances.size).toBe(currentStoreSize);
  });

  storeTest("can remove an instance", async ({ instanceStore }) => {
    const currentStoreSize = instanceStore.instances.size;
    await instanceStore.remove(instanceSeed.entries[0].uid);
    expect(instanceStore.instances.size).toEqual(currentStoreSize - 1);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ instanceStore }) => {
    expect(() => instanceStore.get("EntityNotFoundException")).rejects.toThrow(
      EntityNotFoundException,
    );
  });

  storeTest("correctly reports instanceOptions", async ({ instanceStore }) => {
    expect(instanceStore.instanceOptions.length).toBe(instanceSeed.entries.length);
  });
});
