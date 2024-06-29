import { createPinia, setActivePinia } from "pinia";
import { storeTest } from "../fixtures";
import { imageSeed } from "../seeds";
import { BinaryScale, BinarySizedValue, EntityNotFoundException } from "@/base_types";
import { ImageCreateSchema, ImageModifySchema } from "@/store/images";

describe("Image Store Tests", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  storeTest("returns a cached image", async ({ imageStore }) => {
    const cached = imageSeed.entries[0].name;
    imageSeed.entries[0].name = "updated";
    expect((await imageStore.get(imageSeed.entries[0].uid)).name).toEqual(cached);
  });

  storeTest("can be foreced to update the image", async ({ imageStore }) => {
    imageSeed.entries[0].name = "updated again";
    expect((await imageStore.get(imageSeed.entries[0].uid, true)).name).toEqual(
      imageSeed.entries[0].name,
    );
    expect(imageStore.images.size).toBe(imageSeed.entries.length);
  });

  storeTest("can create an image", async ({ imageStore }) => {
    const currentStoreSize = imageStore.images.size;
    const currentPendingSize = imageStore.pendingImages.size;
    const create = new ImageCreateSchema(
      "Test Image",
      "https://test/image",
      2,
      new BinarySizedValue(2, BinaryScale.M),
      new BinarySizedValue(2, BinaryScale.M),
    );
    const created = await imageStore.create(create);
    expect(created.uid).toBeDefined();
    expect(imageStore.images.size).toBe(currentStoreSize);
    expect(imageStore.pendingImages.size).toBe(currentPendingSize + 1);
  });

  storeTest("can modify an image", async ({ imageStore }) => {
    const currentStoreSize = imageStore.images.size;
    imageSeed.entries[0].name = "Modified";
    const modified = await imageStore.modify(
      imageSeed.entries[0].uid,
      new ImageModifySchema(imageSeed.entries[0]),
    );
    expect(modified.uid).toBeDefined();
    expect(modified.name).toEqual(imageSeed.entries[0].name);
    expect(modified.path).toEqual(imageSeed.entries[0].path);
    expect(modified.url).toEqual(imageSeed.entries[0].url);
    expect(modified.min_vcpu).toEqual(imageSeed.entries[0].min_vcpu);
    expect(modified.min_ram).toEqual(imageSeed.entries[0].min_ram);
    expect(modified.min_disk).toEqual(imageSeed.entries[0].min_disk);
    expect(imageStore.images.size).toBe(currentStoreSize);
  });

  storeTest("can remove an identity", async ({ imageStore }) => {
    const currentStoreSize = imageStore.images.size;
    await imageStore.remove(imageSeed.entries[0].uid);
    expect(imageStore.images.size).toEqual(currentStoreSize - 1);
  });

  storeTest("raises an error for a EntityNotFoundException", async ({ imageStore }) => {
    expect(() => imageStore.get("EntityNotFoundException")).rejects.toThrow(
      EntityNotFoundException,
    );
  });

  storeTest("correctly reports identityOptions", async ({ imageStore }) => {
    expect(imageStore.imageOptions.length).toBe(imageSeed.entries.length);
  });
});
