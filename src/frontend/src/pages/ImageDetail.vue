<script setup lang="ts">
import { onMounted, ref, Ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ImageGetSchema,
  ImageCreateSchema,
  ImageModifySchema,
  useImageStore,
} from "@/store/images";
import { TaskGetSchema, useTaskStore } from "@/store/tasks";
import { ConfigSchema, PredefinedImageSchema, useConfigStore } from "@/store/config";
import { BinaryScale } from "@/base_types";

const imageStore = useImageStore();
const taskStore = useTaskStore();
const configStore = useConfigStore();
const router = useRouter();
const route = useRoute();

const readMode: Ref<boolean> = ref(true);
const modifyMode: Ref<boolean> = ref(false);
const createMode: Ref<boolean> = ref(false);
const busy: Ref<boolean> = ref(false);
const showRemoveConfirmationDialog: Ref<boolean> = ref(false);
const editForm = ref(null);

const title: Ref<string> = ref("Image Detail");

const config: Ref<ConfigSchema> = ref({} as ConfigSchema);
const predefined_images: Ref<PredefinedImageSchema[]> = ref([] as PredefinedImageSchema[]);
const predefined_image: Ref<PredefinedImageSchema | null> = ref(null);
const uid: Ref<string> = ref("");
const original: Ref<ImageGetSchema> = ref({} as ImageGetSchema);
const model: Ref<any> = ref(new ImageGetSchema());

async function onBack() {
  await router.push({ name: "Images" });
}

async function onCancel() {
  if (createMode.value) {
    createMode.value = false;
    await onBack();
    return;
  }
  model.value = original.value;
  title.value = "Image: " + model.value.name;
  readMode.value = true;
  modifyMode.value = false;
}

async function onRemove() {
  busy.value = true;
  imageStore.remove(uid.value).then(() => {
    busy.value = false;
    onBack();
  });
}

async function onEdit() {
  title.value = "Modify Image: " + model.value.name;
  model.value = new ImageModifySchema(original.value);
  readMode.value = false;
  modifyMode.value = true;
}

async function onSubmit() {
  readMode.value = true;
  if (createMode.value) {
    imageStore.create(model.value).then(async () => {
      readMode.value = false;
      await onBack();
    });
  } else {
    imageStore.modify(uid.value, model.value).then(() => {
      readMode.value = false;
      onBack();
    });
  }
}

onMounted(async () => {
  config.value = await configStore.get();
  predefined_images.value = config.value.predefined_images;

  if ("uid" in route.params) {
    // We're showing or editing an existing entity
    readMode.value = true;
    modifyMode.value = false;
    createMode.value = false;
    uid.value = route.params.uid as string;
    original.value = await imageStore.get(uid.value);
    model.value = original.value;
    title.value = "Image: " + model.value.name;
  } else {
    // We're creating a new entity
    readMode.value = false;
    modifyMode.value = false;
    createMode.value = true;
    model.value = new ImageCreateSchema();
    title.value = "Create Image";
  }
});
</script>

<template>
  <q-dialog v-model="showRemoveConfirmationDialog" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm">Are you sure you want to remove this image?</span>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="Cancel" color="primary" v-close-popup />
        <q-btn flat label="Remove" color="primary" v-close-popup @click="onRemove" />
      </q-card-actions>
    </q-card>
  </q-dialog>

  <q-form ref="editForm" autofocus @submit.prevent="onSubmit" style="max-width: 600px">
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
          v-show="readMode || modifyMode"
          :model-value="uid"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-input
          name="name"
          label="Name"
          tabindex="1"
          autofocus
          :hint="readMode ? '' : 'A unique name for the image'"
          :clearable="modifyMode || createMode"
          :readonly="readMode"
          v-model="model.name"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="path"
          label="Path"
          tabindex="-1"
          :hint="readMode ? '' : 'The image path on local disk'"
          :clearable="modifyMode"
          :readonly="readMode"
          v-show="readMode"
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
          tabindex="2"
          emit-value
          map-options
          :hint="readMode ? '' : 'Predefined image URLs'"
          :readonly="readMode"
          :options="predefined_images"
          option-label="name"
          option-value="url"
          v-show="createMode"
          v-model="predefined_image"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="url"
          label="Custom Image URL"
          tabindex="3"
          :hint="readMode ? '' : 'Image URL'"
          :clearable="createMode"
          :readonly="readMode"
          v-show="createMode || readMode"
          v-model="model.url"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-xl">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-slider
          name="min_vcpu"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="4"
          :hint="readMode ? '' : 'Minimum vCPUs'"
          :readonly="readMode"
          :min="0"
          :step="1"
          :max="10"
          :label-value="'Minimum vCPUs: ' + model.min_vcpu"
          v-model="model.min_vcpu"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md" style="padding-top: 30px">
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="min_ram_value"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="5"
          :hint="readMode ? '' : 'Minimum RAM'"
          :readonly="readMode"
          :min="0"
          :step="1"
          :max="16"
          :label-value="'Minimum RAM: ' + model.min_ram.value + ' ' + model.min_ram.scale"
          v-model="model.min_ram.value"
        />
      </div>
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-select
          name="min_ram_scale"
          label="Scale"
          tabindex="6"
          :readonly="readMode"
          :options="Object.values(BinaryScale)"
          v-model="model.min_ram.scale"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md" style="padding-top: 30px">
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="min_disk_value"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="7"
          :hint="readMode ? '' : 'Minimum Disk size'"
          :readonly="readMode"
          :min="0"
          :step="1"
          :max="16"
          :label-value="'Minimum Disk: ' + model.min_disk.value + ' ' + model.min_disk.scale"
          v-model="model.min_disk.value"
        />
      </div>
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-select
          name="min_disk_scale"
          label="Scale"
          tabindex="8"
          :readonly="readMode"
          :options="Object.values(BinaryScale)"
          v-model="model.min_disk.scale"
        />
      </div>
    </div>
    <div
      class="row q-gutter-xl q-col-gutter-x-md q-col-gutter-y-md justify-end"
      style="padding-top: 30px"
    >
      <q-btn
        class="form-button"
        padding="lg"
        size="md"
        label="Edit"
        color="accent"
        tabindex="8"
        v-show="readMode"
        @click="onEdit"
      />
      <q-btn
        class="form-button"
        padding="lg"
        label="Remove"
        color="warning"
        tabindex="9"
        v-show="readMode"
        @click="showRemoveConfirmationDialog = true"
      />
      <q-btn
        class="form-button"
        padding="lg"
        label="Cancel"
        color="secondary"
        tabindex="10"
        v-show="modifyMode || createMode"
        @click="onCancel"
      />
      <q-btn
        class="form-button"
        padding="lg"
        :label="createMode ? 'Create' : 'Modify'"
        type="submit"
        color="primary"
        tabindex="11"
        v-show="modifyMode || createMode"
        :loading="busy"
      >
        <template v-slot:loading>
          <q-spinner />
        </template>
      </q-btn>
    </div>
  </q-form>
</template>

<style scoped>
.form-button {
  min-width: 200px;
}
</style>
