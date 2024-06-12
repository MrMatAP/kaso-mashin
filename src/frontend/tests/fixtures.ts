import { test } from "vitest";
import { http, HttpHandler, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import {
  BootstrapCreateSchema,
  BootstrapGetSchema,
  BootstrapModifySchema,
  useBootstrapStore,
} from "@/store/bootstraps";
import { useTaskStore } from "@/store/tasks";
import {
  EntityInvariantException,
  EntityNotFoundException,
  ExceptionKind,
  KasoMashinException,
  ListableEntity,
} from "@/base_types";
import { bootstrapSeed, taskSeed } from "./seeds";

function mockAPICollectionHandler(base: string, seed: ListableEntity): HttpHandler {
  return http.get(base, () => HttpResponse.json(seed));
}

function mockAPIResourceHandler(base: string, seed: ListableEntity): HttpHandler {
  return http.get(base, ({ params }) => {
    switch (params.uid as string) {
      case ExceptionKind.KASOMASHIN:
        return HttpResponse.json(new KasoMashinException(400, "General Exception"), {
          status: 400,
        });
      case ExceptionKind.ENTITYNOTFOUND:
        return HttpResponse.json(new EntityNotFoundException(404, "Not Found"), { status: 404 });
      case ExceptionKind.ENTITYINVARIANT:
        return HttpResponse.json(new EntityInvariantException(404, "Entity Invariant"), {
          status: 400,
        });
      default:
        return HttpResponse.json(seed.entries[parseInt(params.uid as string)]);
    }
  });
}

const mockAPIHandlers: HttpHandler[] = [
  mockAPICollectionHandler("/api/tasks/", taskSeed),
  mockAPIResourceHandler("/api/tasks/:uid", taskSeed),
  mockAPICollectionHandler("/api/bootstraps/", bootstrapSeed),
  mockAPIResourceHandler("/api/bootstraps/:uid", bootstrapSeed),
  http.post("/api/bootstraps/", async ({ request }) => {
    const create = (await request.json()) as BootstrapCreateSchema;
    return HttpResponse.json(
      new BootstrapGetSchema(crypto.randomUUID(), create.name, create.kind, create.content),
      { status: 201 },
    );
  }),
  http.put("/api/bootstraps/:uid", async ({ request }) => {
    const modify = (await request.json) as BootstrapModifySchema;
  }),
];
const server = setupServer(...mockAPIHandlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

type TaskStore = ReturnType<typeof useTaskStore>;
type BootstrapStore = ReturnType<typeof useBootstrapStore>;

interface StoreFixtures {
  taskStore: TaskStore;
  bootstrapStore: BootstrapStore;
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
  },
});
