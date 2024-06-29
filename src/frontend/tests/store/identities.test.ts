import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { identitySeed } from "../seeds";
import { EntityNotFoundException } from "@/base_types";
import { IdentityCreateSchema, IdentityKind, IdentityModifySchema } from "@/store/identities";

describe("Identity Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached identity", async ({ identityStore }) => {
    const cached = identitySeed.entries[0].name;
    identitySeed.entries[0].name = "updated";
    expect((await identityStore.get(identitySeed.entries[0].uid)).name).toEqual(cached);
  });

  storeTest("can be foreced to update the entity", async ({ identityStore }) => {
    identitySeed.entries[0].name = "updated again";
    expect((await identityStore.get(identitySeed.entries[0].uid, true)).name).toEqual(
      identitySeed.entries[0].name,
    );
    expect(identityStore.identities.size).toBe(identitySeed.entries.length);
  });

  storeTest("can create an identity", async ({ identityStore }) => {
    const currentStoreSize = identityStore.identities.size;
    const create = new IdentityCreateSchema(
      "identity",
      IdentityKind.PUBKEY,
      "Test Identity",
      "/home/identity",
      "/bin/bash",
      "MIIfoo",
    );
    const created = await identityStore.create(create);
    expect(created.uid).toBeDefined();
    expect(created.name).toEqual(create.name);
    expect(created.kind).toEqual(create.kind);
    expect(created.gecos).toEqual(create.gecos);
    expect(created.homedir).toEqual(create.homedir);
    expect(created.shell).toEqual(create.shell);
    expect(created.credential).toEqual(create.credential);
    expect(identityStore.identities.size).toBe(currentStoreSize + 1);
  });

  storeTest("can modify an identity", async ({ identityStore }) => {
    const currentStoreSize = identityStore.identities.size;
    const create = new IdentityCreateSchema(
      "identity",
      IdentityKind.PUBKEY,
      "Test Identity",
      "/home/identity",
      "/bin/bash",
      "MIIfoo",
    );
    const created = await identityStore.create(create);
    created.name = "Modified";
    const modified = await identityStore.modify(created.uid, new IdentityModifySchema(created));
    expect(modified.uid).toBeDefined();
    expect(modified.name).toEqual(created.name);
    expect(modified.kind).toEqual(created.kind);
    expect(modified.gecos).toEqual(created.gecos);
    expect(modified.homedir).toEqual(created.homedir);
    expect(modified.shell).toEqual(created.shell);
    expect(modified.credential).toEqual(created.credential);
    expect(identityStore.identities.size).toBe(currentStoreSize + 1);
  });

  storeTest("can remove an identity", async ({ identityStore }) => {
    const currentStoreSize = identityStore.identities.size;
    await identityStore.remove(identitySeed.entries[0].uid);
    expect(identityStore.identities.size).toEqual(currentStoreSize - 1);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ identityStore }) => {
    expect(() => identityStore.get("EntityNotFoundException")).rejects.toThrow(
      EntityNotFoundException,
    );
  });

  storeTest("correctly reports identityOptions", async ({ identityStore }) => {
    expect(identityStore.identityOptions.length).toBe(identitySeed.entries.length);
  });
});
