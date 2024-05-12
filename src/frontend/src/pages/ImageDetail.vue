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
import {
  ConfigSchema,
  PredefinedImageSchema,
  useConfigStore,
} from "@/store/config";
import { BinaryScale } from "@/base_types";

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
const predefined_images: Ref<PredefinedImageSchema[]> = ref(
  [] as PredefinedImageSchema[],
);
const predefined_image: Ref<PredefinedImageSchema | null> = ref(null);
const uid: Ref<string> = ref("");
const original: Ref<ImageGetSchema> = ref({} as ImageGetSchema);
const model: Ref<ImageGetSchema | ImageCreateSchema | ImageModifySchema> = ref(
  new ImageCreateSchema(),
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
    store.create(model.value).then((task) => {
      readonly.value = false;
      console.dir(task);
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
  config.value = await configStore.get();
  predefined_images.value = config.value.predefined_images;

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
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="path"
          label="Path"
          tabindex="2"
          v-show="model instanceof ImageGetSchema"
          :hint="readonly ? '' : 'The image path on local disk'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.path"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-select
          name="predefined"
          label="Predefined Image URLs"
          clearable
          tabindex="3"
          emit-value
          map-options
          :hint="readonly ? '' : 'Predefined image URLs'"
          :readonly="readonly"
          :options="predefined_images"
          option-label="name"
          option-value="url"
          v-model="model.url"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="url"
          label="Custom Image URL"
          tabindex="4"
          :hint="readonly ? '' : 'Image URL'"
          :clearable="!readonly"
          :readonly="readonly || !predefined_image"
          v-model="model.url"
        />
      </div>
    </div>
    <div
      class="row q-col-gutter-x-md q-col-gutter-y-xl"
      style="padding-top: 30px"
    >
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-slider
          name="min_vcpu"
          label
          label-always
          markers
          snap
          tabindex="4"
          :hint="readonly ? '' : 'Minimum vCPUs'"
          :readonly="readonly"
          :min="0"
          :step="1"
          :max="10"
          :label-value="'Minimum vCPUs: ' + model.min_vcpu"
          v-model="model.min_vcpu"
        />
      </div>
    </div>
    <div
      class="row q-col-gutter-x-md q-col-gutter-y-md"
      style="padding-top: 30px"
    >
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="min_ram_value"
          label
          label-always
          markers
          snap
          tabindex="5"
          :hint="readonly ? '' : 'Minimum RAM'"
          :readonly="readonly"
          :min="0"
          :step="1"
          :max="16"
          :label-value="
            'Minimum RAM: ' + model.min_ram.value + ' ' + model.min_ram.scale
          "
          v-model="model.min_ram.value"
        />
      </div>
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-select
          name="min_ram_scale"
          label="Scale"
          tabindex="6"
          :readonly="readonly"
          :options="Object.values(BinaryScale)"
          v-model="model.min_ram.scale"
        />
      </div>
    </div>
    <div
      class="row q-col-gutter-x-md q-col-gutter-y-md"
      style="padding-top: 30px"
    >
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="min_disk_value"
          label
          label-always
          markers
          snap
          tabindex="5"
          :hint="readonly ? '' : 'Minimum Disk size'"
          :readonly="readonly"
          :min="0"
          :step="1"
          :max="16"
          :label-value="
            'Minimum Disk: ' + model.min_disk.value + ' ' + model.min_disk.scale
          "
          v-model="model.min_disk.value"
        />
      </div>
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-select
          name="min_disk_scale"
          label="Scale"
          tabindex="6"
          :readonly="readonly"
          :options="Object.values(BinaryScale)"
          v-model="model.min_disk.scale"
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
