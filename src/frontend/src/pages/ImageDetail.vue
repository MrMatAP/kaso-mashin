<script setup lang="ts">
import { onMounted, ref, Ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { BinaryScale, FormMode } from "@/base_types";
import {
  ImageGetSchema,
  ImageCreateSchema,
  ImageModifySchema,
  useImageStore,
} from "@/store/images";
import { ConfigSchema, PredefinedImageSchema, useConfigStore } from "@/store/config";

const imageStore = useImageStore();
const configStore = useConfigStore();
const router = useRouter();
const route = useRoute();

const mode: Ref<FormMode> = ref(FormMode.READ);
const busy: Ref<boolean> = ref(false);
const showRemoveConfirmationDialog: Ref<boolean> = ref(false);
const detailForm = ref(null);

const title = computed(() => {
  switch (mode.value) {
    case FormMode.READ:
      return `Image: ${original.value.name}`;
    case FormMode.EDIT:
      return `Modify Image: ${original.value.name}`;
    case FormMode.CREATE:
      return "Create Image";
    default:
      return "Image Detail";
  }
});

const uid: Ref<string> = ref("");
const original: Ref<ImageGetSchema> = ref({} as ImageGetSchema);
const model: Ref<any> = ref(new ImageGetSchema());

const config: Ref<ConfigSchema> = ref({} as ConfigSchema);
const predefined_images: Ref<PredefinedImageSchema[]> = ref([] as PredefinedImageSchema[]);
const predefined_url: Ref<string> = ref("");

async function onBack() {
  await router.push({ name: "Images" });
}

async function onCancel() {
  if (mode.value == FormMode.CREATE) {
    await onBack();
    return;
  }
  model.value = original.value;
  mode.value = FormMode.READ;
}

async function onRemove() {
  busy.value = true;
  imageStore.remove(uid.value).then(async () => {
    busy.value = false;
    await onBack();
  });
}

async function onEdit() {
  model.value = new ImageModifySchema(original.value);
  mode.value = FormMode.EDIT;
}

async function onSubmit() {
  busy.value = true;
  if (mode.value == FormMode.CREATE) {
    imageStore.create(model.value).then(async () => {
      mode.value = FormMode.READ;
      busy.value = false;
      await onBack();
    });
  } else {
    imageStore.modify(uid.value, model.value).then(async () => {
      mode.value = FormMode.READ;
      busy.value = false;
      await onBack();
    });
  }
}

function onPredefinedImageUpdate() {
  if (predefined_url.value !== "") {
    model.value.url = predefined_url.value;
  }
}

onMounted(async () => {
  busy.value = true;
  config.value = await configStore.get();
  predefined_images.value = config.value.predefined_images;

  if ("uid" in route.params) {
    mode.value = FormMode.READ;
    uid.value = route.params.uid as string;
    original.value = await imageStore.get(uid.value);
    model.value = original.value;
  } else {
    mode.value = FormMode.CREATE;
    model.value = new ImageCreateSchema();
  }
  busy.value = false;
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
        <q-btn flat label="Remove" color="negative" v-close-popup @click="onRemove" />
      </q-card-actions>
    </q-card>
  </q-dialog>

  <q-form ref="detailForm" class="detail-form" autofocus @submit.prevent="onSubmit">
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
          v-show="mode !== FormMode.CREATE"
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
          :hint="mode == FormMode.READ ? '' : 'A unique name for this image'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.name"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-select
          name="predefined"
          label="Predefined Image"
          clearable
          tabindex="2"
          emit-value
          map-options
          :hint="mode == FormMode.READ ? '' : 'Predefined image URLs'"
          :readonly="mode == FormMode.READ"
          :options="predefined_images"
          option-label="name"
          option-value="url"
          v-show="mode == FormMode.CREATE"
          v-model="predefined_url"
          @update:model-value="onPredefinedImageUpdate"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="url"
          label="Custom Image URL"
          tabindex="3"
          :hint="mode == FormMode.READ ? '' : 'Image URL'"
          :clearable="mode == FormMode.CREATE"
          :readonly="mode !== FormMode.CREATE"
          v-show="mode == FormMode.CREATE"
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
          :hint="mode == FormMode.READ ? '' : 'Minimum vCPUs'"
          :readonly="mode == FormMode.READ"
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
          :hint="mode == FormMode.READ ? '' : 'Minimum RAM'"
          :readonly="mode == FormMode.READ"
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
          :readonly="mode == FormMode.READ"
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
          :hint="mode == FormMode.READ ? '' : 'Minimum Disk size'"
          :readonly="mode == FormMode.READ"
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
          :readonly="mode == FormMode.READ"
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
        class="detail-form-button"
        label="Edit"
        color="primary"
        tabindex="8"
        v-show="mode == FormMode.READ"
        @click="onEdit"
      />
      <q-btn
        class="detail-form-button"
        label="Remove"
        color="negative"
        tabindex="9"
        v-show="mode == FormMode.READ"
        @click="showRemoveConfirmationDialog = true"
      />
      <q-btn
        class="detail-form-button"
        label="Cancel"
        color="primary"
        tabindex="10"
        v-show="mode !== FormMode.READ"
        @click="onCancel"
      />
      <q-btn
        class="detail-form-button"
        :label="mode == FormMode.CREATE ? 'Create' : 'Modify'"
        type="submit"
        color="positive"
        tabindex="11"
        v-show="mode !== FormMode.READ"
        :loading="busy"
      >
        <template v-slot:loading>
          <q-spinner />
        </template>
      </q-btn>
    </div>
  </q-form>

  <q-markup-table v-show="mode == FormMode.READ" class="detail-metadata">
    <thead>
      <tr>
        <th colspan="2" class="text-left"><h6>Metadata</h6></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="text-left">Image Path</td>
        <td class="text-left">{{ model.path }}</td>
      </tr>
      <tr>
        <td class="text-left">Image Source URL</td>
        <td class="text-left">{{ model.url }}</td>
      </tr>
    </tbody>
  </q-markup-table>
</template>
