<script setup lang="ts">
import { onMounted, ref, Ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  NetworkCreateSchema,
  NetworkGetSchema,
  NetworkModifySchema,
  NetworkKind,
  useNetworkStore,
} from "@/store/networks";

const networksStore = useNetworkStore();
const router = useRouter();
const route = useRoute();

const readMode: Ref<boolean> = ref(true);
const modifyMode: Ref<boolean> = ref(false)
const createMode: Ref<boolean> = ref(false)
const busy: Ref<boolean> = ref(false);
const pendingConfirmation: Ref<boolean> = ref(false);
const editForm = ref(null);

const title: Ref<string> = ref("Network Detail");
const uid: Ref<string> = ref("");
const original: Ref<NetworkGetSchema> = ref(new NetworkGetSchema());
const model: Ref<any> = ref(new NetworkGetSchema());

async function onBack() {
  await router.push({ name: "Networks" });
}

async function onCancel() {
  if (createMode.value) {
    createMode.value = false;
    await onBack();
    return;
  }
  model.value = original.value;
  title.value = "Network: " + model.value.name;
  readMode.value = true;
  modifyMode.value = false;
}

async function onRemove() {
  busy.value = true;
  networksStore.remove(uid.value).then(() => {
    busy.value = false;
    onBack();
  });
}

async function onEdit() {
  title.value = "Modify Network: " + model.value.name;
  model.value = new NetworkModifySchema(original.value);
  readMode.value = false;
  modifyMode.value = true;
}

async function onSubmit() {
  readMode.value = true;
  if (createMode.value) {
    networksStore.create(model.value).then(() => {
      readMode.value = false;
      onBack();
    });
  } else {
    networksStore.modify(uid.value, model.value).then(() => {
      readMode.value = false;
      onBack();
    });
  }
}

onMounted(async () => {
  busy.value = true
  if ("uid" in route.params) {
    // We're showing or editing an existing identity
    readMode.value = true;
    modifyMode.value = false;
    createMode.value = false;
    uid.value = route.params.uid as string;
    original.value = await networksStore.get(uid.value);
    model.value = original.value;
    title.value = "Network: " + model.value.name;
  } else {
    // We're creating a new identity
    readMode.value = false;
    modifyMode.value = false;
    createMode.value = true;
    model.value = new NetworkCreateSchema();
    title.value = "Create Network";
  }
  busy.value = false;
});
</script>

<template>
  <q-dialog v-model="pendingConfirmation" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm"
          >Are you sure you want to remove this network?</span
        >
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
          :hint="readMode ? '' : 'A unique name for the network'"
          :clearable="modifyMode || createMode"
          :readonly="readMode"
          v-model="model.name"
        />
      </div>
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-select
          name="kind"
          label="Kind"
          tabindex="1"
          :hint="readMode ? '' : 'Network kind'"
          :readonly="readMode"
          :options="Object.values(NetworkKind)"
          v-show="true"
          v-model="model.kind"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="cidr"
          label="CIDR"
          tabindex="2"
          :hint="readMode ? '' : 'The network CIDR'"
          :clearable="modifyMode || createMode"
          :readonly="readMode"
          v-model="model.cidr"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="gateway"
          label="Gateway Address"
          tabindex="3"
          :hint="readMode ? '' : 'Network gateway address'"
          :clearable="!readMode"
          :readonly="readMode"
          v-model="model.gateway"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="dhcp_start"
          label="DHCP Start Address"
          tabindex="4"
          :hint="readMode ? '' : 'DHCP start address'"
          :clearable="modifyMode || createMode"
          :readonly="readMode"
          v-model="model.dhcp_start"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="dhcp_end"
          label="DHCP End Address"
          tabindex="5"
          :hint="readMode ? '' : 'DHCP end address'"
          :clearable="modifyMode || createMode"
          :readonly="readMode"
          v-model="model.dhcp_end"
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
        @click="pendingConfirmation = true"
      />
      <q-btn
        flat
        padding="lg"
        label="Cancel"
        color="secondary"
        v-show="!readMode"
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
