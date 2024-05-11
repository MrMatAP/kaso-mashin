<script setup lang="ts">
import { onMounted, ref, Ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ImageGetSchema,
  ImageCreateSchema,
  ImageModifySchema,
  useImagesStore,
} from "@/store/images";
import { TaskGetSchema, useTasksStore } from "@/store/tasks";
import { ConfigSchema, useConfigStore } from "@/store/config";

const store = useImagesStore();
const tasksStore = useTasksStore();
const configStore = useConfigStore();
const router = useRouter();
const route = useRoute();

const readonly: Ref<boolean> = ref(true);
const busy: Ref<boolean> = ref(false);
const pendingConfirmation: Ref<boolean> = ref(false);

const title: Ref<string> = ref("Image Detail");
const editForm = ref(null);

const config: Ref<ConfigSchema> = ref({} as ConfigSchema);
const predefined_urls: Ref<Map<string, string>> = ref(new Map());
const predefined_url: Ref<String> = ref("");
const uid: Ref<string> = ref("");
const original: Ref<ImageGetSchema> = ref({} as ImageGetSchema);
const model: Ref<ImageGetSchema | ImageCreateSchema | ImageModifySchema> = ref(
  {} as ImageCreateSchema,
);

async function onBack() {
  await router.push({ name: "Images" });
}

async function onCancel() {
  if (model.value instanceof ImageCreateSchema) {
    await onBack();
    return;
  }
  model.value = original.value;
  title.value = "Image: " + model.value.name;
  readonly.value = true;
}

async function onRemove() {
  busy.value = true;
  store.remove(uid.value).then(() => {
    busy.value = false;
    onBack();
  });
}

async function onEdit() {
  title.value = "Modify Image: " + model.value.name;
  model.value = new ImageModifySchema(original.value);
  readonly.value = false;
}

async function onSubmit() {
  readonly.value = true;
  if (model.value instanceof ImageCreateSchema) {
    store.create(model.value).then(() => {
      readonly.value = false;
      onBack();
    });
  } else {
    store.modify(uid.value, model.value).then(() => {
      readonly.value = false;
      onBack();
    });
  }
}

onMounted(async () => {
  if ("uid" in route.params) {
    // We're showing or editing an existing identity
    readonly.value = true;
    uid.value = route.params.uid as string;
    original.value = await store.get(uid.value);
    model.value = original.value;
    title.value = "Image: " + model.value.name;
  } else {
    // We're creating a new identity
    readonly.value = false;
    model.value = new ImageCreateSchema();
    title.value = "Create Image";
    config.value = await configStore.get();
    predefined_urls.value = config.value.predefined_images;
    console.log(predefined_urls.value);
  }
});
</script>

<template>
  <q-dialog v-model="pendingConfirmation" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm">Are you sure you want to remove this image?</span>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="Cancel" color="primary" v-close-popup />
        <q-btn
          flat
          label="Remove"
          color="primary"
          v-close-popup
          @click="onRemove"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>

  <q-form
    ref="editForm"
    autofocus
    @submit.prevent="onSubmit"
    style="max-width: 600px"
  >
    <div class="row nowrap">
      <q-btn flat icon="arrow_back_ios" @click="onBack"></q-btn>
      <h4>{{ title }}</h4>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="uid"
          label="UID"
          readonly
          v-show="uid"
          :model-value="uid"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-input
          name="name"
          label="Name"
          tabindex="0"
          autofocus
          :hint="readonly ? '' : 'A unique name for the image'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.name"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="path"
          label="Path"
          tabindex="2"
          :hint="readonly ? '' : 'The image path on local disk'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.path"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="url"
          label="URL"
          tabindex="3"
          :hint="readonly ? '' : 'Image URL'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.url"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-select
          name="predefined"
          label="Predefined Image URLs"
          tabindex="4"
          :hint="readonly ? '' : 'Predefined image URLs'"
          :readonly="readonly"
          :options="config.predefined_images"
          option-label="name"
          option-value="url"
          v-model="model.url"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-input
          name="min_vcpu"
          label="Minimum vCPUs"
          tabindex="4"
          :hint="readonly ? '' : 'Minimum vCPUs'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.min_vcpu"
        />
      </div>
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-input
          name="min_ram"
          label="Minimum RAM"
          tabindex="5"
          :hint="readonly ? '' : 'Minimum RAM'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.min_ram"
        />
      </div>
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-input
          name="min_disk"
          label="Minimum Disk"
          tabindex="5"
          :hint="readonly ? '' : 'Minimum Disk'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.min_disk"
        />
      </div>
    </div>
    <div class="row q-gutter-xl justify-end">
      <q-btn
        flat
        padding="lg"
        label="Edit"
        color="primary"
        v-show="readonly"
        @click="onEdit"
      />
      <q-btn
        flat
        padding="lg"
        label="Remove"
        color="primary"
        v-show="readonly"
        @click="pendingConfirmation = true"
      />
      <q-btn
        flat
        padding="lg"
        label="Cancel"
        color="secondary"
        v-show="!readonly"
        @click="onCancel"
      />
      <q-btn
        flat
        padding="lg"
        :label="model instanceof ImageCreateSchema ? 'Create' : 'Modify'"
        type="submit"
        color="primary"
        v-show="!readonly"
        :loading="busy"
      >
        <template v-slot:loading>
          <q-spinner />
        </template>
      </q-btn>
    </div>
  </q-form>
</template>

<style scoped></style>
