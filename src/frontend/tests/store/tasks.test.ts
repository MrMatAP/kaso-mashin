import { createPinia, setActivePinia } from "pinia";
import { TaskGetSchema, TaskRelation, TaskState, useTaskStore } from "@/store/tasks";
import { http, HttpHandler, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import {
  EntityInvariantException,
  EntityNotFoundException,
  KasoMashinException,
} from "@/base_types";

const seed: TaskGetSchema[] = [
  {
    uid: "0",
    name: "task 0",
    msg: "task zero",
    relation: TaskRelation.BOOTSTRAPS,
    state: TaskState.RUNNING,
    percent_complete: 50,
  },
  {
    uid: "1",
    name: "task 1",
    msg: "task one",
    relation: TaskRelation.INSTANCES,
    state: TaskState.DONE,
    percent_complete: 100,
  },
  {
    uid: "2",
    name: "task 2",
    msg: "task two",
    relation: TaskRelation.IDENTITIES,
    state: TaskState.FAILED,
    percent_complete: 10,
  },
];

export const restHandlers: HttpHandler[] = [
  http.get("http://localhost:3000/api/tasks/", () => {
    return HttpResponse.json({ entries: seed });
  }),
  http.get("http://localhost:3000/api/tasks/0", () => {
    return HttpResponse.json(seed[0]);
  }),
  http.get("http://localhost:3000/api/tasks/1", () => {
    return HttpResponse.json(seed[1]);
  }),
  http.get("http://localhost:3000/api/tasks/2", () => {
    return HttpResponse.json(seed[2]);
  }),
  http.get("http://localhost:3000/api/tasks/KasoMashinException", () => {
    return HttpResponse.json(new KasoMashinException(400, "KasoMashinException"), { status: 400 });
  }),
  http.get("http://localhost:3000/api/tasks/EntityNotFoundException", () => {
    return HttpResponse.json(new EntityNotFoundException(404, "Not Found"), { status: 404 });
  }),
  http.get("http://localhost:3000/api/tasks/EntityInvariantException", () => {
    return HttpResponse.json(new EntityInvariantException(404, "EntityInvariantException"), {
      status: 400,
    });
  }),
];

const server = setupServer(...restHandlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

describe("Task Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("fetches tasks", async () => {
    const taskStore = useTaskStore();
    expect(taskStore.tasks.size).toBe(0);
    await taskStore.list();
    expect(taskStore.tasks.size).toBe(seed.length);
  });

  it("returns a cached task", async () => {
    const taskStore = useTaskStore();
    expect(taskStore.tasks.size).toBe(0);
    await taskStore.list();
    expect(taskStore.tasks.size).toBe(seed.length);
    expect(taskStore.tasks.get(seed[0].uid)).toStrictEqual(seed[0]);
    const cached_value = seed[0].percent_complete;
    seed[0].percent_complete = 80;
    expect((await taskStore.get(seed[0].uid)).percent_complete).toEqual(cached_value); // no forced update
  });

  it("can be forced to update the task", async () => {
    const taskStore = useTaskStore();
    expect(taskStore.tasks.size).toBe(0);
    await taskStore.list();
    expect(taskStore.tasks.size).toBe(seed.length);
    expect(taskStore.tasks.get(seed[0].uid)).toStrictEqual(seed[0]);
    seed[0].percent_complete = 80;
    expect((await taskStore.get(seed[0].uid, true)).percent_complete).toEqual(
      seed[0].percent_complete,
    );
    expect(taskStore.tasks.size).toBe(seed.length);
  });

  it("correctly reports allTasks", async () => {
    const taskStore = useTaskStore();
    await taskStore.list();
    expect(taskStore.tasks.size).toBe(seed.length);
    expect(taskStore.allTasks.length).toBe(seed.length);
  });

  it("correctly reports runningTasks", async () => {
    const taskStore = useTaskStore();
    await taskStore.list();
    const running = seed.filter((task) => task.state === TaskState.RUNNING);
    expect(taskStore.runningTasks.length).toBe(running.length);
  });

  it("correctly reports failedTasks", async () => {
    const taskStore = useTaskStore();
    await taskStore.list();
    const failed = seed.filter((task) => task.state === TaskState.FAILED);
    expect(taskStore.failedTasks.length).toBe(failed.length);
  });

  it("correctly reports doneTasks", async () => {
    const taskStore = useTaskStore();
    await taskStore.list();
    const done = seed.filter((task) => task.state === TaskState.DONE);
    expect(taskStore.doneTasks.length).toBe(done.length);
  });

  it("raises an error for a KasoMashinException", async () => {
    const taskStore = useTaskStore();
    expect(() => taskStore.get("KasoMashinException")).rejects.toThrow(KasoMashinException);
  });

  it("raises an error for a EntityNotFoundException", async () => {
    const taskStore = useTaskStore();
    expect(() => taskStore.get("EntityNotFoundException")).rejects.toThrow(EntityNotFoundException);
  });

  it("raises an error for a EntityInvariantException", async () => {
    const taskStore = useTaskStore();
    expect(() => taskStore.get("EntityInvariantException")).rejects.toThrow(
      EntityInvariantException,
    );
  });
});
