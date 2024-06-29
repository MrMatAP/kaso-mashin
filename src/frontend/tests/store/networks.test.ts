import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { networkSeed } from "../seeds";
import { NetworkCreateSchema, NetworkKind, NetworkModifySchema } from "@/store/networks";
import {
  EntityInvariantException,
  EntityNotFoundException,
  KasoMashinException,
} from "@/base_types";
import { BootstrapModifySchema } from "@/store/bootstraps";

describe("Network Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached network", async ({ networkStore }) => {
    const seeded = networkSeed.entries[0].cidr;
    networkSeed.entries[0].cidr = "1.2.2.4";
    expect((await networkStore.get(networkSeed.entries[0].uid)).cidr).toEqual(seeded);
  });

  storeTest("can be forced to update the network", async ({ networkStore }) => {
    networkSeed.entries[0].cidr = "4.2.2.1";
    const foo = await networkStore.get(networkSeed.entries[0].uid, true);
    expect((await networkStore.get(networkSeed.entries[0].uid, true)).cidr).toEqual(
      networkSeed.entries[0].cidr,
    );
    expect(networkStore.networks.size).toBe(networkSeed.entries.length);
  });

  storeTest("can create a network", async ({ networkStore }) => {
    const currentStoreSize = networkStore.networks.size;
    const create = new NetworkCreateSchema(
      "Test Network Create",
      NetworkKind.VMNET_BRIDGED,
      "1.0.0.0/8",
      "1.0.0.1",
      "1.0.0.10",
      "1.0.0.254",
    );
    const created = await networkStore.create(create);
    expect(created.uid).toBeDefined();
    expect(created.name).toEqual(create.name);
    expect(created.kind).toEqual(create.kind);
    expect(created.cidr).toEqual(create.cidr);
    expect(created.gateway).toEqual(create.gateway);
    expect(created.dhcp_start).toEqual(create.dhcp_start);
    expect(created.dhcp_end).toEqual(create.dhcp_end);
    expect(networkStore.networks.size).toBe(currentStoreSize + 1);
  });

  storeTest("can modify a network", async ({ networkStore }) => {
    const currentStoreSize = networkStore.networks.size;
    const create = new NetworkCreateSchema(
      "Test Network Modify",
      NetworkKind.VMNET_HOST,
      "2.0.0.0/8",
      "2.0.0.1",
      "2.0.0.10",
      "2.0.0.254",
    );
    const created = await networkStore.create(create);
    created.name = "Modified";
    const modified = await networkStore.modify(created.uid, new NetworkModifySchema(created));
    expect(modified.uid).toEqual(created.uid);
    expect(modified.name).toEqual("Modified");
    expect(modified.kind).toEqual(created.kind);
    expect(modified.gateway).toEqual(created.gateway);
    expect(modified.dhcp_start).toEqual(created.dhcp_start);
    expect(modified.dhcp_end).toEqual(created.dhcp_end);
    expect(networkStore.networks.size).toEqual(currentStoreSize + 1);
  });

  storeTest("can remove a network", async ({ networkStore }) => {
    const currentStoreSize = networkStore.networks.size;
    await networkStore.remove(networkSeed.entries[0].uid);
    expect(networkStore.networks.size).toEqual(currentStoreSize - 1);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ networkStore }) => {
    expect(() => networkStore.get("EntityNotFoundException")).rejects.toThrow(
      EntityNotFoundException,
    );
  });

  storeTest("correctly reports networkOptions", async ({ networkStore }) => {
    expect(networkStore.networkOptions.length).toBe(networkSeed.entries.length);
  });
});
