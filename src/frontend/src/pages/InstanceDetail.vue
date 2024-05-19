<script setup lang="ts">
import { onMounted, Ref, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  InstanceGetSchema,
  InstanceCreateSchema,
  InstanceModifySchema,
  useInstanceStore,
} from "@/store/instances";
import {
  NetworkGetSchema,
  useNetworkStore
} from "@/store/networks";
import {
  DiskGetSchema,
  useDiskStore,
} from "@/store/disks";
import {
  ImageGetSchema,
  useImageStore
} from '@/store/images'
import {
  BootstrapGetSchema,
  useBootstrapStore
} from "@/store/bootstraps";
import { BinaryScale } from '@/base_types'

const instanceStore = useInstanceStore();
const networkStore = useNetworkStore();
const diskStore = useDiskStore();
const imageStore = useImageStore();
const bootstrapStore = useBootstrapStore();
const router = useRouter();
const route = useRoute();

const readMode: Ref<boolean> = ref(true);
const modifyMode: Ref<boolean> = ref(false)
const createMode: Ref<boolean> = ref(false)
const busy: Ref<boolean> = ref(false);
const showRemoveConfirmationDialog: Ref<boolean> = ref(false);
const editForm = ref(null)

const title: Ref<string> = ref("Instance Detail");

const uid: Ref<string> = ref("");
const original: Ref<InstanceGetSchema> = ref({} as InstanceGetSchema);
const model: Ref<any> = ref(new InstanceGetSchema());
const networkModel: Ref<NetworkGetSchema> = ref(new NetworkGetSchema());
const osDiskModel: Ref<DiskGetSchema> = ref(new DiskGetSchema());
const imageModel: Ref<ImageGetSchema> = ref(new ImageGetSchema());
const bootstrapModel: Ref<BootstrapGetSchema> = ref(new BootstrapGetSchema());

async function onGoNetwork() {
  await router.push({ name: "NetworkDetail", params: { uid: model.value.network_uid } })
}

async function onGoImage() {
  await router.push({ name: 'ImageDetail', params: { uid: osDiskModel.value.image_uid } })
}

async function onGoBootstrap() {
  await router.push({ name: 'BootstrapDetail', params: { uid: model.value.bootstrap_uid } });
}

async function onBack() {
  await router.push({ name: "Instances" });
}

async function onCancel() {
  if (createMode.value) {
    createMode.value = false;
    await onBack();
    return;
  }
  model.value = original.value;
  title.value = "Instance: " + model.value.name;
  readMode.value = true;
  modifyMode.value = false;
}

async function onRemove() {
  busy.value = true;
  instanceStore.remove(uid.value).then(() => {
    busy.value = false;
    onBack();
  });
}

async function onEdit() {
  title.value = "Modify Instance: " + model.value.name;
  model.value = new InstanceModifySchema(original.value);
  readMode.value = false;
  modifyMode.value = true;
}

async function onSubmit() {
  readMode.value = true;
  if (createMode.value) {
    instanceStore.create(model.value).then(async (task) => {
      readMode.value = false;
      await onBack();
    });
  } else {
    instanceStore.modify(uid.value, model.value).then(() => {
      readMode.value = false;
      onBack();
    });
  }
}

onMounted(async () => {
  if ("uid" in route.params) {
    // We're showing or editing an existing entity
    readMode.value = true;
    modifyMode.value = false;
    createMode.value = false;
    uid.value = route.params.uid as string;
    original.value = await instanceStore.get(uid.value);
    model.value = original.value;
    imageModel.value = await imageStore.get(model.value.image_uid)
    networkModel.value = await networkStore.get(model.value.network_uid)
    osDiskModel.value = await diskStore.get(model.value.os_disk_uid)
    bootstrapModel.value = await bootstrapStore.get(model.value.bootstrap_uid)
    title.value = "Instance: " + model.value.name;
  } else {
    // We're creating a new entity
    readMode.value = false;
    modifyMode.value = false;
    createMode.value = true;
    model.value = new InstanceCreateSchema();
    title.value = "Create Instance";
  }
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
      <div class="col-xs-12 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-input
          name="uid"
          label="UID"
          readonly
          v-show="readMode || modifyMode"
          :model-value="uid"
        />
      </div>
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-input
          name="name"
          label="Name"
          tabindex="0"
          autofocus
          :hint="readMode ? '' : 'A unique name for the instance'"
          :clearable="modifyMode || createMode"
          :readonly="readMode"
          v-model="model.name"
        />
      </div>
    </div>
    <div
      class="row q-col-gutter-x-md q-col-gutter-y-xl"
      style="padding-top: 30px"
    >
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-slider
          name="vcpu"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="4"
          :hint="readMode ? '' : 'vCPUs'"
          :readonly="readMode"
          :min="0"
          :step="1"
          :max="10"
          :label-value="'vCPUs: ' + model.vcpu"
          v-model="model.vcpu"
        />
      </div>
    </div>
    <div
      class="row q-col-gutter-x-md q-col-gutter-y-xl"
      style="padding-top: 30px"
    >
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="ram_value"
          label
          label-always
          switch-label-side
          markers
          snap
          tabindex="5"
          :hint="readMode ? '' : 'RAM'"
          :readonly="readMode"
          :min="0"
          :step="1"
          :max="16"
          :label-value="
              'RAM: ' + model.ram.value + ' ' + model.ram.scale
            "
          v-model="model.ram.value"
        />
      </div>
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4 vertical-middle">
        <q-select
          name="ram_scale"
          label="Scale"
          tabindex="6"
          :readonly="readMode"
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
          tabindex="6"
          :readonly="readMode"
          :options="networkStore.networkOptions"
          option-label="name"
          option-value="uid"
          emit-value
          map-options
          v-model="model.network_uid"
        />
      </div>
      <div class="col-xs-2 col-sm-2 col-md-2 col-lg-2 col-xl-2">
        <q-btn flat
               icon="arrow_forward_ios"
               :disable="createMode || modifyMode"
               @click="onGoNetwork"></q-btn>
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-10 col-sm-10 col-md-10 col-lg-10 col-xl-10">
        <q-select name="os_disk_image"
                 label="OS Disk Image"
                 tabindex="3"
                 :hint="readMode ? '' : 'The OS Disk Image'"
                 :readonly="readMode"
                 :options="imageStore.imageOptions"
                 option-label="name"
                 option-value="uid"
                 emit-value
                 map-options
                 v-show="readMode || createMode"
                 v-model="model.image_uid"/>
      </div>
      <div class="col-xs-2 col-sm-2 col-md-2 col-lg-2 col-xl-2">
        <q-btn flat
               icon="arrow_forward_ios"
               :disable="createMode || modifyMode"
               @click="onGoImage"></q-btn>
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
          tabindex="5"
          :hint="readMode ? '' : 'OS Disk Size'"
          :readonly="readMode"
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
          tabindex="6"
          :readonly="readMode"
          :options="Object.values(BinaryScale)"
          v-model="model.os_disk_size.scale"
        />
      </div>
    </div>

    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-10 col-sm-10 col-md-10 col-lg-10 col-xl-10">
        <q-select name="bootstrap_uid"
                  label="Bootstrap"
                  tabindex="3"
                  :hint="readMode ? '' : 'The Bootstrapper'"
                  :readonly="readMode"
                  :options="bootstrapStore.bootstrapOptions"
                  option-label="name"
                  option-value="uid"
                  emit-value
                  map-options
                  v-show="readMode || createMode"
                  v-model="model.bootstrap_uid"/>
      </div>
      <div class="col-xs-2 col-sm-2 col-md-2 col-lg-2 col-xl-2">
        <q-btn flat
               icon="arrow_forward_ios"
               :disable="createMode || modifyMode"
               @click="onGoBootstrap"></q-btn>
      </div>
    </div>
    <div class="row q-gutter-xl justify-end">
      <q-btn
        flat
        padding="lg"
        label="Edit"
        color="primary"
        v-show="readMode"
        @click="onEdit"
      />
      <q-btn
        flat
        padding="lg"
        label="Remove"
        color="primary"
        v-show="readMode"
        @click="showRemoveConfirmationDialog = true"
      />
      <q-btn
        flat
        padding="lg"
        label="Cancel"
        color="secondary"
        v-show="modifyMode || createMode"
        @click="onCancel"
      />
      <q-btn
        flat
        padding="lg"
        :label="createMode ? 'Create' : 'Modify'"
        type="submit"
        color="primary"
        v-show="!readMode"
        :loading="busy"
      >
        <template v-slot:loading>
          <q-spinner />
        </template>
      </q-btn>
    </div>
  </q-form>
  <q-separator/>
  <h5>Instance Metadata</h5>
  <q-markup-table>
    <tbody>
    <tr>
      <td class="text-left">Instance Path</td>
      <td class="text-right">{{ model.path }}</td>
    </tr>
    <tr>
      <td class="text-left">OS Disk Path</td>
      <td class="text-right">{{ osDiskModel.path }}</td>
    </tr>
    <tr>
      <td class="text-left">Bootstrap File Path</td>
      <td class="text-right">{{ model.bootstrap_file }}</td>
    </tr>
    <tr>
      <td class="text-left">MAC Address</td>
      <td class="text-right">{{ model.mac }}</td>
    </tr>
    </tbody>
  </q-markup-table>
</template>

<style scoped></style>
