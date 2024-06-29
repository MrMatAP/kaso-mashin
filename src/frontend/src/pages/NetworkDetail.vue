<script setup lang="ts">
import { onMounted, ref, Ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { FormMode } from "@/base_types";
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

const mode: Ref<FormMode> = ref(FormMode.READ);
const busy: Ref<boolean> = ref(false);
const showRemoveConfirmationDialog: Ref<boolean> = ref(false);
const detailForm = ref(null);

const title = computed(() => {
  switch (mode.value) {
    case FormMode.READ:
      return `Network: ${original.value.name}`;
    case FormMode.EDIT:
      return `Modify Network: ${original.value.name}`;
    case FormMode.CREATE:
      return "Create Network";
    default:
      return "Network Detail";
  }
});

const uid: Ref<string> = ref("");
const original: Ref<NetworkGetSchema> = ref(new NetworkGetSchema());
const model: Ref<any> = ref(new NetworkGetSchema());

async function onBack() {
  await router.push({ name: "Networks" });
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
  networksStore.remove(uid.value).then(async () => {
    busy.value = false;
    await onBack();
  });
}

async function onEdit() {
  model.value = new NetworkModifySchema(original.value);
  mode.value = FormMode.EDIT;
}

async function onSubmit() {
  busy.value = true;

  if (mode.value == FormMode.CREATE) {
    networksStore.create(model.value).then(async () => {
      mode.value = FormMode.READ;
      busy.value = false;
      await onBack();
    });
  } else {
    networksStore.modify(uid.value, model.value).then(async () => {
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
    original.value = await networksStore.get(uid.value);
    model.value = original.value;
  } else {
    mode.value = FormMode.CREATE;
    model.value = new NetworkCreateSchema();
  }
  busy.value = false;
});
</script>

<template>
  <q-dialog v-model="showRemoveConfirmationDialog" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm">Are you sure you want to remove this network?</span>
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
          :hint="mode == FormMode.READ ? '' : 'A unique name for the network'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.name"
        />
      </div>
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-select
          name="kind"
          label="Kind"
          tabindex="2"
          :hint="mode == FormMode.READ ? '' : 'Network Kind'"
          :readonly="mode == FormMode.READ"
          :options="Object.values(NetworkKind)"
          v-model="model.kind"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="cidr"
          label="CIDR"
          tabindex="3"
          :hint="mode == FormMode.READ ? '' : 'The network CIDR'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.cidr"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="gateway"
          label="Gateway Address"
          tabindex="4"
          :hint="mode == FormMode.READ ? '' : 'Network gateway address'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.gateway"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="dhcp_start"
          label="DHCP Start Address"
          tabindex="5"
          :hint="mode == FormMode.READ ? '' : 'DHCP start address'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.dhcp_start"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="dhcp_end"
          label="DHCP End Address"
          tabindex="6"
          :hint="mode == FormMode.READ ? '' : 'DHCP end address'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.dhcp_end"
        />
      </div>
    </div>
    <div class="row q-gutter-xl justify-end">
      <q-btn
        class="detail-form-button"
        label="Edit"
        color="primary"
        tabindex="7"
        v-show="mode == FormMode.READ"
        @click="onEdit"
      />
      <q-btn
        class="detail-form-button"
        label="Remove"
        color="negative"
        tabindex="8"
        v-show="mode == FormMode.READ"
        @click="showRemoveConfirmationDialog = true"
      />
      <q-btn
        class="detail-form-button"
        label="Cancel"
        color="primary"
        tabindex="9"
        v-show="mode !== FormMode.READ"
        @click="onCancel"
      />
      <q-btn
        class="detail-form-button"
        :label="mode == FormMode.CREATE ? 'Create' : 'Modify'"
        type="submit"
        color="positive"
        tabindex="10"
        v-show="mode !== FormMode.READ"
        :loading="busy"
      >
        <template v-slot:loading>
          <q-spinner />
        </template>
      </q-btn>
    </div>
  </q-form>
</template>
