import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { networkSeed } from "../seeds";
import { NetworkCreateSchema, NetworkKind, NetworkModifySchema } from "@/store/networks";
import {
  EntityInvariantException,
  EntityNotFoundException,
  KasoMashinException,
} from "@/base_types";

describe("Network Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached network", async ({ networkStore }) => {
    const cached = networkSeed.entries[0].cidr;
    networkSeed.entries[0].cidr = "1.2.2.4";
    expect((await networkStore.get(networkSeed.entries[0].uid)).cidr).toEqual(cached);
  });

  storeTest("can be forced to update the entity", async ({ networkStore }) => {
    networkSeed.entries[0].cidr = "4.2.2.1";
    const foo = await networkStore.get(networkSeed.entries[0].uid, true);
    expect((await networkStore.get(networkSeed.entries[0].uid, true)).cidr).toEqual(
      networkSeed.entries[0].cidr,
    );
    expect(networkStore.networks.size).toBe(networkSeed.entries.length);
  });
});
