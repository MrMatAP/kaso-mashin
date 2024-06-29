import { test } from "vitest";
import { http, HttpHandler, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import {
  CreatableEntity,
  Entity,
  EntityNotFoundException,
  ListableEntity,
  ModifiableEntity,
} from "@/base_types";

import { TaskGetSchema, TaskRelation, TaskState, useTaskStore } from "@/store/tasks";
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

import {
  bootstrapSeed,
  diskSeed,
  identitySeed,
  imageSeed,
  instanceSeed,
  networkSeed,
  taskSeed,
} from "./seeds";
import {
  IdentityCreateSchema,
  IdentityGetSchema,
  IdentityListSchema,
  IdentityModifySchema,
  useIdentityStore,
} from "@/store/identities";
import {
  ImageCreateSchema,
  ImageGetSchema,
  ImageListSchema,
  ImageModifySchema,
  useImageStore,
} from "@/store/images";
import {
  DiskCreateSchema,
  DiskGetSchema,
  DiskListSchema,
  DiskModifySchema,
  useDiskStore,
} from "@/store/disks";
import {
  InstanceCreateSchema,
  InstanceGetSchema,
  InstanceListSchema,
  InstanceModifySchema,
  InstanceState,
  useInstanceStore,
} from "@/store/instances";

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
    const modified = this.modify_fn(current, entity);
    this.entities.set(uid, modified);
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
>(
  (create: NetworkCreateSchema) =>
    new NetworkGetSchema(
      crypto.randomUUID(),
      create.name,
      create.kind,
      create.cidr,
      create.gateway,
      create.dhcp_start,
      create.dhcp_end,
    ),
  (current: NetworkGetSchema, modify: NetworkModifySchema) =>
    new NetworkGetSchema(
      current.uid,
      modify.name,
      modify.kind,
      modify.cidr,
      modify.gateway,
      modify.dhcp_start,
      modify.dhcp_end,
    ),
  networkSeed,
);

const mockBootstrapAPI = new MockGenericAPI<
  BootstrapListSchema,
  BootstrapGetSchema,
  BootstrapCreateSchema,
  BootstrapModifySchema
>(
  (create: BootstrapCreateSchema) =>
    new BootstrapGetSchema(crypto.randomUUID(), create.name, create.kind, create.content),
  (current: BootstrapGetSchema, modify: BootstrapModifySchema) =>
    new BootstrapGetSchema(current.uid, modify.name, modify.kind, modify.content),
  bootstrapSeed,
);

const mockIdentityAPI = new MockGenericAPI<
  IdentityListSchema,
  IdentityGetSchema,
  IdentityCreateSchema,
  IdentityModifySchema
>(
  (create: IdentityCreateSchema) =>
    new IdentityGetSchema(
      crypto.randomUUID(),
      create.name,
      create.kind,
      create.gecos,
      create.homedir,
      create.shell,
      create.credential,
    ),
  (current: IdentityGetSchema, modify: IdentityModifySchema) =>
    new IdentityGetSchema(
      current.uid,
      modify.name,
      modify.kind,
      modify.gecos,
      modify.homedir,
      modify.shell,
      modify.credential,
    ),
  identitySeed,
);

const mockImageAPI = new MockGenericAPI<
  ImageListSchema,
  ImageGetSchema,
  ImageCreateSchema,
  ImageModifySchema
>(
  (create: ImageCreateSchema) =>
    new TaskGetSchema(
      crypto.randomUUID(),
      "download task",
      TaskRelation.IMAGES,
      TaskState.RUNNING,
      `Downloading image ${create.name}`,
    ),
  (current: ImageGetSchema, modify: ImageModifySchema) =>
    new ImageGetSchema(
      current.uid,
      modify.name,
      current.path,
      current.url,
      modify.min_vcpu | modify.min_vcpu,
      modify.min_ram,
      modify.min_disk,
    ),
  imageSeed,
);

const mockDiskAPI = new MockGenericAPI<
  DiskListSchema,
  DiskGetSchema,
  DiskCreateSchema,
  DiskModifySchema
>(
  (create: DiskCreateSchema) =>
    new DiskGetSchema(
      crypto.randomUUID(),
      create.name,
      "/path/to/img",
      create.size,
      create.disk_format,
      create.image_uid,
    ),
  (current: DiskGetSchema, modify: DiskModifySchema) =>
    new DiskGetSchema(
      current.uid,
      modify.name,
      current.path,
      modify.size,
      current.disk_format,
      current.image_uid,
    ),
  diskSeed,
);

const mockInstanceAPI = new MockGenericAPI<
  InstanceListSchema,
  InstanceGetSchema,
  InstanceCreateSchema,
  InstanceModifySchema
>(
  (create: InstanceCreateSchema) =>
    new InstanceGetSchema(
      crypto.randomUUID(),
      create.name,
      `/path/to/${create.name}`,
      create.vcpu,
      create.ram,
      "00:00:00:00:01:00",
      crypto.randomUUID(),
      create.os_disk_size,
      create.network_uid,
      create.bootstrap_uid,
      "/path/to/bootstrap",
      InstanceState.STOPPED,
    ),
  (current: InstanceGetSchema, modify: InstanceModifySchema) =>
    new InstanceGetSchema(
      current.uid,
      modify.name,
      current.path,
      modify.vcpu,
      modify.ram,
      current.mac,
      current.os_disk_uid,
      current.os_disk_size,
      current.network_uid,
      current.bootstrap_uid,
      current.bootstrap_file,
    ),
  instanceSeed,
);

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
  ...mockIdentityAPI.handlers("/api/identities"),
  ...mockImageAPI.handlers("/api/images"),
  ...mockDiskAPI.handlers("/api/disks"),
  ...mockInstanceAPI.handlers("/api/instances"),
];
const server = setupServer(...mockAPIHandlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

type TaskStore = ReturnType<typeof useTaskStore>;
type BootstrapStore = ReturnType<typeof useBootstrapStore>;
type NetworkStore = ReturnType<typeof useNetworkStore>;
type IdentityStore = ReturnType<typeof useIdentityStore>;
type ImageStore = ReturnType<typeof useImageStore>;
type DiskStore = ReturnType<typeof useDiskStore>;
type InstanceStore = ReturnType<typeof useInstanceStore>;

interface StoreFixtures {
  taskStore: TaskStore;
  bootstrapStore: BootstrapStore;
  networkStore: NetworkStore;
  identityStore: IdentityStore;
  imageStore: ImageStore;
  diskStore: DiskStore;
  instanceStore: InstanceStore;
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
  identityStore: async ({}, use) => {
    const identityStore = useIdentityStore();
    expect(identityStore.identities.size).toBe(0);
    await identityStore.list();
    expect(identityStore.identities.size).toBe(identitySeed.entries.length);
    await use(identityStore);
    mockIdentityAPI.reset();
  },
  imageStore: async ({}, use) => {
    const imageStore = useImageStore();
    expect(imageStore.images.size).toBe(0);
    await imageStore.list();
    expect(imageStore.images.size).toBe(imageSeed.entries.length);
    await use(imageStore);
    mockImageAPI.reset();
  },
  diskStore: async ({}, use) => {
    const diskStore = useDiskStore();
    expect(diskStore.disks.size).toBe(0);
    await diskStore.list();
    expect(diskStore.disks.size).toBe(diskSeed.entries.length);
    await use(diskStore);
    mockDiskAPI.reset();
  },
  instanceStore: async ({}, use) => {
    const instanceStore = useInstanceStore();
    expect(instanceStore.instances.size).toBe(0);
    await instanceStore.list();
    expect(instanceStore.instances.size).toBe(instanceSeed.entries.length);
    await use(instanceStore);
    mockInstanceAPI.reset();
  },
});
