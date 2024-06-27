import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { bootstrapSeed } from "../seeds";
import { BootstrapCreateSchema, BootstrapKind, BootstrapModifySchema } from "@/store/bootstraps";
import { EntityNotFoundException } from "@/base_types";

describe("Bootstrap Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached bootstrap", async ({ bootstrapStore }) => {
    const cached = bootstrapSeed.entries[0].content;
    bootstrapSeed.entries[0].content = "updated";
    expect((await bootstrapStore.get(bootstrapSeed.entries[0].uid)).content).toEqual(cached); // no forced update
  });

  storeTest("can be forced to update the bootstrap", async ({ bootstrapStore }) => {
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
    expect(modified.kind).toEqual(created.kind);
    expect(modified.name).toEqual(modified.name);
    expect(bootstrapStore.bootstraps.size).toEqual(currentStoreSize + 1);
  });

  storeTest("can remove a bootstrap", async ({ bootstrapStore }) => {
    const currentStoreSize = bootstrapStore.bootstraps.size;
    await bootstrapStore.remove(bootstrapSeed.entries[0].uid);
    expect(bootstrapStore.bootstraps.size).toEqual(currentStoreSize - 1);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ bootstrapStore }) => {
    expect(() => bootstrapStore.get("EntityNotFoundException")).rejects.toThrow(
      EntityNotFoundException,
    );
  });

  storeTest("correctly reports bootstrapOptions", async ({ bootstrapStore }) => {
    expect(bootstrapStore.bootstrapOptions.length).toBe(bootstrapSeed.entries.length);
  });
});
