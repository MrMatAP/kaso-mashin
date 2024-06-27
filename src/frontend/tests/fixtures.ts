import { test } from "vitest";
import { http, HttpHandler, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import {
  CreatableEntity,
  Entity,
  EntityInvariantException,
  EntityNotFoundException,
  ExceptionKind,
  KasoMashinException,
  ListableEntity,
  ModifiableEntity,
} from "@/base_types";

import { useTaskStore } from "@/store/tasks";
import {
  BootstrapCreateSchema,
  BootstrapGetSchema,
  BootstrapListSchema,
  BootstrapModifySchema,
  useBootstrapStore,
} from "@/store/bootstraps";
import {
  NetworkCreateSchema,
  NetworkGetSchema,
  NetworkListSchema,
  NetworkModifySchema,
  useNetworkStore,
} from "@/store/networks";

import { bootstrapSeed, networkSeed, taskSeed } from "./seeds";
import {
  IdentityCreateSchema,
  IdentityGetSchema,
  IdentityListSchema,
  IdentityModifySchema,
} from "@/store/identities";

function createBootstrapFn(entity: BootstrapCreateSchema): BootstrapGetSchema {
  return new BootstrapGetSchema(crypto.randomUUID(), entity.name, entity.kind, entity.content);
}

function modifyBootstrapFn(uid: string, entity: BootstrapModifySchema): BootstrapGetSchema {
  return new BootstrapGetSchema(uid, entity.name, entity.kind, entity.content);
}

function createNetworkFn(entity: NetworkCreateSchema): NetworkGetSchema {
  return new NetworkGetSchema(
    crypto.randomUUID(),
    entity.name,
    entity.kind,
    entity.cidr,
    entity.gateway,
    entity.dhcp_start,
    entity.dhcp_end,
  );
}

function modifyNetworkFn(uid: string, entity: NetworkModifySchema): NetworkGetSchema {
  return new NetworkGetSchema(
    uid,
    entity.name,
    entity.kind,
    entity.cidr,
    entity.gateway,
    entity.dhcp_start,
    entity.dhcp_end,
  );
}

class MockGenericAPI<
  L extends ListableEntity<G>,
  G extends Entity,
  C extends CreatableEntity,
  M extends ModifiableEntity<G>,
> {
  entities: Map<string, G>;
  create_fn: Function;
  modify_fn: Function;
  seed?: L;

  constructor(create_fn: Function, modify_fn: Function, seed?: L) {
    this.entities = new Map<string, G>();
    this.create_fn = create_fn;
    this.modify_fn = modify_fn;
    this.seed = seed;
    this.reset();
  }

  reset() {
    this.entities.clear();
    if (this.seed) this.seed.entries.forEach((s) => this.entities.set(s.uid, s));
  }

  list() {
    return HttpResponse.json({ entries: Array.from<G>(this.entities.values()) });
  }

  get(uid: string) {
    if (!this.entities.has(uid))
      return HttpResponse.json(new EntityNotFoundException(404, "Not found"), { status: 404 });
    return HttpResponse.json(this.entities.get(uid));
  }

  create(entity: C) {
    const created = this.create_fn(entity);
    this.entities.set(created.uid, created);
    return HttpResponse.json(created, { status: 201 });
  }

  modify(uid: string, entity: M) {
    const current = this.entities.get(uid);
    if (!current)
      return HttpResponse.json(new EntityNotFoundException(404, "Not found"), { status: 404 });
    const modified = this.modify_fn(uid, entity);
    this.entities.set(uid, this.modify_fn(uid, entity));
    return HttpResponse.json(modified, { status: 200 });
  }

  remove(uid: string) {
    if (!this.entities.has(uid)) return HttpResponse.json({}, { status: 410 });
    return HttpResponse.json({}, { status: 210 });
  }

  handlers(base: string): HttpHandler[] {
    return [
      http.get(`${base}/`, () => this.list()),
      http.get(`${base}/:uid`, ({ params }) => this.get(params.uid as string)),
      http.post(`${base}/`, async ({ request }) => {
        const create = (await request.json()) as C;
        return this.create(create);
      }),
      http.put(`${base}/:uid`, async ({ params, request }) => {
        const modify = (await request.json()) as M;
        return this.modify(params.uid as string, modify);
      }),
      http.delete(`${base}/:uid`, ({ params }) => this.remove(params.uid as string)),
    ];
  }
}

const mockNetworkAPI = new MockGenericAPI<
  NetworkListSchema,
  NetworkGetSchema,
  NetworkCreateSchema,
  NetworkModifySchema
>(createNetworkFn, modifyNetworkFn, networkSeed);

const mockBootstrapAPI = new MockGenericAPI<
  BootstrapListSchema,
  BootstrapGetSchema,
  BootstrapCreateSchema,
  BootstrapModifySchema
>(createBootstrapFn, modifyBootstrapFn, bootstrapSeed);

const mockAPIHandlers: HttpHandler[] = [
  http.get("/api/tasks/", () => HttpResponse.json(taskSeed)),
  http.get("/api/tasks/:uid", ({ params }) => {
    const seed = taskSeed.entries.find((seed) => seed.uid === params.uid);
    if (seed == undefined)
      return HttpResponse.json(new EntityNotFoundException(404, "Not Found"), { status: 404 });
    return HttpResponse.json(seed, { status: 200 });
  }),
  ...mockBootstrapAPI.handlers("/api/bootstraps"),
  ...mockNetworkAPI.handlers("/api/networks"),
];
const server = setupServer(...mockAPIHandlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

type TaskStore = ReturnType<typeof useTaskStore>;
type BootstrapStore = ReturnType<typeof useBootstrapStore>;
type NetworkStore = ReturnType<typeof useNetworkStore>;

interface StoreFixtures {
  taskStore: TaskStore;
  bootstrapStore: BootstrapStore;
  networkStore: NetworkStore;
}

export const storeTest = test.extend<StoreFixtures>({
  taskStore: async ({}, use) => {
    const taskStore = useTaskStore();
    expect(taskStore.tasks.size).toBe(0);
    await taskStore.list();
    expect(taskStore.tasks.size).toBe(taskSeed.entries.length);
    await use(taskStore);
  },
  bootstrapStore: async ({}, use) => {
    const bootstrapStore = useBootstrapStore();
    expect(bootstrapStore.bootstraps.size).toBe(0);
    await bootstrapStore.list();
    expect(bootstrapStore.bootstraps.size).toBe(bootstrapSeed.entries.length);
    await use(bootstrapStore);
    mockBootstrapAPI.reset();
  },
  networkStore: async ({}, use) => {
    const networkStore = useNetworkStore();
    expect(networkStore.networks.size).toBe(0);
    await networkStore.list();
    expect(networkStore.networks.size).toBe(networkSeed.entries.length);
    await use(networkStore);
    mockNetworkAPI.reset();
  },
});
