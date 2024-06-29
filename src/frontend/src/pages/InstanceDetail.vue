<script setup lang="ts">
import { onMounted, Ref, ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { BinaryScale, FormMode } from "@/base_types";
import {
  InstanceGetSchema,
  InstanceCreateSchema,
  InstanceModifySchema,
  useInstanceStore,
} from "@/store/instances";
import { NetworkGetSchema, useNetworkStore } from "@/store/networks";
import { DiskGetSchema, useDiskStore } from "@/store/disks";
import { ImageGetSchema, useImageStore } from "@/store/images";
import { BootstrapGetSchema, useBootstrapStore } from "@/store/bootstraps";

const instanceStore = useInstanceStore();
const networkStore = useNetworkStore();
const diskStore = useDiskStore();
const imageStore = useImageStore();
const bootstrapStore = useBootstrapStore();
const router = useRouter();
const route = useRoute();

const mode: Ref<FormMode> = ref(FormMode.READ);
const busy: Ref<boolean> = ref(false);
const showRemoveConfirmationDialog: Ref<boolean> = ref(false);
const detailForm = ref(null);

const title = computed(() => {
  switch (mode.value) {
    case FormMode.READ:
      return `Instance: ${original.value.name}`;
    case FormMode.EDIT:
      return `Modify Instance: ${original.value.name}`;
    case FormMode.CREATE:
      return "Create Instance";
    default:
      return "Instance Detail";
  }
});

const uid: Ref<string> = ref("");
const original: Ref<InstanceGetSchema> = ref({} as InstanceGetSchema);
const model: Ref<any> = ref(new InstanceGetSchema());

const networkModel: Ref<NetworkGetSchema> = ref(new NetworkGetSchema());
const osDiskModel: Ref<DiskGetSchema> = ref(new DiskGetSchema());
const imageModel: Ref<ImageGetSchema> = ref(new ImageGetSchema());
const bootstrapModel: Ref<BootstrapGetSchema> = ref(new BootstrapGetSchema());

async function onGoNetwork() {
  await router.push({ name: "NetworkDetail", params: { uid: model.value.network_uid } });
}

async function onGoImage() {
  await router.push({ name: "ImageDetail", params: { uid: model.value.image_uid } });
}

async function onGoBootstrap() {
  await router.push({ name: "BootstrapDetail", params: { uid: model.value.bootstrap_uid } });
}

async function onBack() {
  await router.push({ name: "Instances" });
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
  instanceStore.remove(uid.value).then(async () => {
    busy.value = false;
    await onBack();
  });
}

async function onEdit() {
  model.value = new InstanceModifySchema(original.value);
  mode.value = FormMode.EDIT;
}

async function onSubmit() {
  busy.value = true;
  if (mode.value == FormMode.CREATE) {
    instanceStore.create(model.value).then(async () => {
      mode.value = FormMode.READ;
      busy.value = false;
      await onBack();
    });
  } else {
    instanceStore.modify(uid.value, model.value).then(async () => {
      mode.value = FormMode.READ;
      busy.value = false;
      await onBack();
    });
  }
}

onMounted(async () => {
  busy.value = true;
  if ("uid" in route.params) {
    mode.value = FormMode.READ;
    uid.value = route.params.uid as string;
    original.value = await instanceStore.get(uid.value);
    model.value = original.value;
    imageModel.value = await imageStore.get(model.value.image_uid);
    networkModel.value = await networkStore.get(model.value.network_uid);
    osDiskModel.value = await diskStore.get(model.value.os_disk_uid);
    bootstrapModel.value = await bootstrapStore.get(model.value.bootstrap_uid);
  } else {
    mode.value = FormMode.CREATE;
    model.value = new InstanceCreateSchema();
  }
  busy.value = false;
});
</script>

<template>
  <q-dialog v-model="showRemoveConfirmationDialog" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm">Are you sure you want to remove this instance?</span>
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
      <div class="col-xs-12 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-input
          name="uid"
          label="UID"
          readonly
          v-show="mode !== FormMode.CREATE"
          :model-value="uid"
        />
      </div>
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-input
          name="name"
          label="Name"
          tabindex="1"
          autofocus
          :hint="mode == FormMode.READ ? '' : 'A unique name for the instance'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.name"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-xl" style="padding-top: 30px">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-slider
          name="vcpu"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="2"
          :hint="mode == FormMode.READ ? '' : 'vCPUs'"
          :readonly="mode == FormMode.READ"
          :min="0"
          :step="1"
          :max="10"
          :label-value="'vCPUs: ' + model.vcpu"
          v-model="model.vcpu"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-xl" style="padding-top: 30px">
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="ram_value"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="3"
          :hint="mode == FormMode.READ ? '' : 'RAM'"
          :readonly="mode == FormMode.READ"
          :min="0"
          :step="1"
          :max="16"
          :label-value="'RAM: ' + model.ram.value + ' ' + model.ram.scale"
          v-model="model.ram.value"
        />
      </div>
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4 vertical-middle">
        <q-select
          name="ram_scale"
          label="Scale"
          tabindex="4"
          :readonly="mode == FormMode.READ"
          :options="Object.values(BinaryScale)"
          v-model="model.ram.scale"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-10 col-sm-10 col-md-10 col-lg-10 col-xl-10">
        <q-select
          name="network"
          label="Network"
          tabindex="5"
          :readonly="mode == FormMode.READ"
          :options="networkStore.networkOptions"
          option-label="name"
          option-value="uid"
          emit-value
          map-options
          v-model="model.network_uid"
        />
      </div>
      <div class="col-xs-2 col-sm-2 col-md-2 col-lg-2 col-xl-2">
        <q-btn
          flat
          icon="arrow_forward_ios"
          tabindex="6"
          v-show="mode == FormMode.READ"
          @click="onGoNetwork"
        ></q-btn>
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-10 col-sm-10 col-md-10 col-lg-10 col-xl-10">
        <q-select
          name="os_disk_image"
          label="OS Disk Image"
          tabindex="7"
          :hint="mode == FormMode.READ ? '' : 'The OS Disk Image'"
          :readonly="mode == FormMode.READ"
          :options="imageStore.imageOptions"
          option-label="name"
          option-value="uid"
          emit-value
          map-options
          v-show="mode !== FormMode.EDIT"
          v-model="model.image_uid"
        />
      </div>
      <div class="col-xs-2 col-sm-2 col-md-2 col-lg-2 col-xl-2">
        <q-btn
          flat
          icon="arrow_forward_ios"
          tabindex="8"
          v-show="mode == FormMode.READ"
          @click="onGoImage"
        ></q-btn>
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="os_disk_size_value"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="9"
          :hint="mode == FormMode.READ ? '' : 'OS Disk Size'"
          :readonly="mode == FormMode.READ"
          :min="0"
          :step="1"
          :max="16"
          :label-value="
            'OS Disk Size: ' + model.os_disk_size.value + ' ' + model.os_disk_size.scale
          "
          v-model="model.os_disk_size.value"
        />
      </div>
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4 vertical-middle">
        <q-select
          name="os_disk_size_scale"
          label="Scale"
          tabindex="10"
          :readonly="mode == FormMode.READ"
          :options="Object.values(BinaryScale)"
          v-model="model.os_disk_size.scale"
        />
      </div>
    </div>

    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-10 col-sm-10 col-md-10 col-lg-10 col-xl-10">
        <q-select
          name="bootstrap_uid"
          label="Bootstrap"
          tabindex="11"
          :hint="mode == FormMode.READ ? '' : 'The Bootstrapper'"
          :readonly="mode == FormMode.READ"
          :options="bootstrapStore.bootstrapOptions"
          option-label="name"
          option-value="uid"
          emit-value
          map-options
          v-show="mode !== FormMode.EDIT"
          v-model="model.bootstrap_uid"
        />
      </div>
      <div class="col-xs-2 col-sm-2 col-md-2 col-lg-2 col-xl-2">
        <q-btn
          flat
          icon="arrow_forward_ios"
          tabindex="12"
          v-show="mode == FormMode.READ"
          @click="onGoBootstrap"
        ></q-btn>
      </div>
    </div>
    <div class="row q-gutter-xl justify-end">
      <q-btn
        class="detail-form-button"
        label="Edit"
        color="primary"
        tabindex="13"
        v-show="mode == FormMode.READ"
        @click="onEdit"
      />
      <q-btn
        class="detail-form-button"
        label="Remove"
        color="negative"
        tabindex="14"
        v-show="mode == FormMode.READ"
        @click="showRemoveConfirmationDialog = true"
      />
      <q-btn
        class="detail-form-button"
        label="Cancel"
        color="primary"
        tabindex="15"
        v-show="mode !== FormMode.READ"
        @click="onCancel"
      />
      <q-btn
        class="detail-form-button"
        :label="mode == FormMode.CREATE ? 'Create' : 'Modify'"
        type="submit"
        color="positive"
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
        <td class="text-left">Instance Path</td>
        <td class="text-left">{{ model.path }}</td>
      </tr>
      <tr>
        <td class="text-left">OS Disk Path</td>
        <td class="text-left">{{ osDiskModel.path }}</td>
      </tr>
      <tr>
        <td class="text-left">Bootstrap File Path</td>
        <td class="text-left">{{ model.bootstrap_file }}</td>
      </tr>
      <tr>
        <td class="text-left">MAC Address</td>
        <td class="text-left">{{ model.mac }}</td>
      </tr>
    </tbody>
  </q-markup-table>
</template>
