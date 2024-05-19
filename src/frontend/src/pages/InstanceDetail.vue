<script setup lang="ts">
import { onMounted, Ref, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  InstanceGetSchema,
  InstanceCreateSchema,
  InstanceModifySchema,
  useInstanceStore,
} from "@/store/instances";
import { TaskGetSchema, useTaskStore } from "@/store/tasks";
import { BinaryScale } from '@/base_types'

const instanceStore = useInstanceStore();
const tasksStore = useTaskStore();
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
          tabindex="0"
          autofocus
          :hint="readMode ? '' : 'A unique name for the instance'"
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
          tabindex="2"
          :hint="readMode ? '' : 'The instance path on local disk'"
          :clearable="modifyMode"
          :readonly="readMode"
          v-show="readMode"
          v-model="model.path"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="bootstrap_file"
          label="Bootstrap file"
          tabindex="2"
          :hint="readMode ? '' : 'The bootstrap file path on local disk'"
          :clearable="modifyMode"
          :readonly="readMode"
          v-show="readMode"
          v-model="model.bootstrap_file"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="mac"
          label="MAC Address"
          tabindex="2"
          :hint="readMode ? '' : 'The MAC address of the primary interface'"
          :clearable="modifyMode"
          :readonly="readMode"
          v-show="readMode"
          v-model="model.mac"
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
      class="row q-col-gutter-x-md q-col-gutter-y-md"
      style="padding-top: 30px"
    >
      <div class="col-xs-8 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-slider
          name="ram_value"
          label
          label-always
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
      <div class="col-xs-4 col-sm-4 col-md-4 col-lg-4 col-xl-4">
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
</template>

<style scoped></style>
