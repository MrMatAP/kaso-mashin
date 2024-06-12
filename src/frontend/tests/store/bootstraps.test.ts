import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { bootstrapSeed } from "../seeds";
import { BootstrapCreateSchema, BootstrapKind, BootstrapModifySchema } from "@/store/bootstraps";
import {
  EntityInvariantException,
  EntityNotFoundException,
  KasoMashinException,
} from "@/base_types";

describe("Bootstrap Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached task", async ({ bootstrapStore }) => {
    expect(bootstrapStore.bootstraps.get(bootstrapSeed.entries[0].uid)).toEqual(
      bootstrapSeed.entries[0],
    );
    const cached_value = bootstrapSeed.entries[0].content;
    bootstrapSeed.entries[0].content = "updated";
    expect((await bootstrapStore.get(bootstrapSeed.entries[0].uid)).content).toEqual(cached_value); // no forced update
  });

  storeTest("can be forced to update the task", async ({ bootstrapStore }) => {
    expect(bootstrapStore.bootstraps.get(bootstrapSeed.entries[0].uid)).toEqual(
      bootstrapSeed.entries[0],
    );
    bootstrapSeed.entries[0].content = "updated again";
    expect((await bootstrapStore.get(bootstrapSeed.entries[0].uid, true)).content).toEqual(
      bootstrapSeed.entries[0].content,
    );
    expect(bootstrapStore.bootstraps.size).toBe(bootstrapSeed.entries.length);
  });

  storeTest("can create a bootstrap", async ({ bootstrapStore }) => {
    const currentStoreSize = bootstrapStore.bootstraps.size;
    const create = new BootstrapCreateSchema(
      "Test Bootstrap",
      BootstrapKind.IGNITION,
      "test content",
    );
    const created = await bootstrapStore.create(create);
    expect(created.uid).toBeDefined();
    expect(created.name).toEqual(create.name);
    expect(created.kind).toEqual(create.kind);
    expect(created.content).toEqual(create.content);
    expect(bootstrapStore.bootstraps.size).toBe(currentStoreSize + 1);
  });

  storeTest("can modify a bootstrap", async ({ bootstrapStore }) => {
    const currentStoreSize = bootstrapStore.bootstraps.size;
    const create = new BootstrapCreateSchema(
      "Test Bootstrap",
      BootstrapKind.CLOUD_INIT,
      "test content",
    );
    const created = await bootstrapStore.create(create);
    created.name = "Modified";
    const modified = await bootstrapStore.modify(created.uid, new BootstrapModifySchema(created));
    expect(modified.uid).toEqual(created.uid);
    expect(modified.name).toEqual(modified.name);
    expect(bootstrapStore.bootstraps.size).toEqual(currentStoreSize);
  });

  storeTest("can remove a bootstrap", async ({ bootstrapStore }) => {
    const currentStoreSize = bootstrapStore.bootstraps.size;
    await bootstrapStore.remove(bootstrapSeed.entries[0].uid);
    expect(bootstrapStore.bootstraps.size).toEqual(currentStoreSize - 1);
    expect(bootstrapStore.get(bootstrapSeed.entries[0].uid)).toThrow(EntityInvariantException);
  });

  storeTest("correctly reports bootstrapOptions", async ({ bootstrapStore }) => {
    expect(bootstrapStore.bootstrapOptions.length).toBe(bootstrapSeed.entries.length);
  });

  storeTest("raises an error for a KasoMashinException", async ({ bootstrapStore }) => {
    expect(() => bootstrapStore.get("KasoMashinException")).rejects.toThrow(KasoMashinException);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ bootstrapStore }) => {
    expect(() => bootstrapStore.get("EntityNotFoundException")).rejects.toThrow(
      EntityNotFoundException,
    );
  });

  storeTest("raises an error for a EntityInvariantException", async ({ bootstrapStore }) => {
    expect(() => bootstrapStore.get("EntityInvariantException")).rejects.toThrow(
      EntityInvariantException,
    );
  });
});
