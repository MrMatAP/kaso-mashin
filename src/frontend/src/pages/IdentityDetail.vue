<script setup lang="ts">
import { onMounted, ref, Ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { FormMode } from "@/base_types";
import {
  IdentityCreateSchema,
  IdentityGetSchema,
  IdentityKind,
  IdentityModifySchema,
  useIdentityStore,
} from "@/store/identities";

const identityStore = useIdentityStore();
const router = useRouter();
const route = useRoute();

const mode: Ref<FormMode> = ref(FormMode.READ);
const busy: Ref<boolean> = ref(false);
const showRemoveConfirmationDialog: Ref<boolean> = ref(false);
const detailForm = ref(null);

const title = computed(() => {
  switch (mode.value) {
    case FormMode.READ:
      return `Identity: ${original.value.name}`;
    case FormMode.EDIT:
      return `Modify Identity: ${original.value.name}`;
    case FormMode.CREATE:
      return "Create Identity";
    default:
      return "Identity Detail";
  }
});

const uid: Ref<string> = ref("");
const original: Ref<IdentityGetSchema> = ref({} as IdentityGetSchema);
const model: Ref<any> = ref(new IdentityGetSchema());

const pwCredential = ref("");
const pubkeyCredential = ref("");
const isPwd = ref(true);

async function onBack() {
  await router.push({ name: "Identities" });
}

async function onCancel() {
  if (mode.value == FormMode.CREATE) {
    await onBack();
    return;
  }
  model.value = original.value;
  pubkeyCredential.value = model.value.kind === IdentityKind.PUBKEY ? model.value.credential : "";
  pwCredential.value = model.value.kind === IdentityKind.PASSWORD ? model.value.credential : "";
  mode.value = FormMode.READ;
}

async function onRemove() {
  busy.value = true;
  identityStore.remove(uid.value).then(async () => {
    busy.value = false;
    await onBack();
  });
}

async function onEdit() {
  model.value = new IdentityModifySchema(original.value);
  pubkeyCredential.value = model.value.kind === IdentityKind.PUBKEY ? model.value.credential : "";
  pwCredential.value = model.value.kind === IdentityKind.PASSWORD ? model.value.credential : "";
  mode.value = FormMode.EDIT;
}

async function onSubmit() {
  busy.value = true;
  model.value.credential =
    model.value.kind === IdentityKind.PUBKEY ? pubkeyCredential.value : pwCredential.value;
  if (mode.value == FormMode.CREATE) {
    identityStore.create(model.value).then(async () => {
      mode.value = FormMode.READ;
      busy.value = false;
      await onBack();
    });
  } else {
    identityStore.modify(uid.value, model.value).then(async () => {
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
    original.value = await identityStore.get(uid.value);
    model.value = original.value;
  } else {
    mode.value = FormMode.CREATE;
    model.value = new IdentityCreateSchema();
  }
  busy.value = false;
});
</script>

<template>
  <q-dialog v-model="showRemoveConfirmationDialog" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm">Are you sure you want to remove this identity?</span>
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
          :hint="mode == FormMode.READ ? '' : 'A unique name for this identity'"
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
          :hint="mode == FormMode.READ ? '' : 'Identity Kind'"
          :readonly="mode == FormMode.READ"
          :options="Object.values(IdentityKind)"
          v-model="model.kind"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="gecos"
          label="GECOS"
          tabindex="3"
          :hint="mode == FormMode.READ ? '' : 'The display name of this identity'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.gecos"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="homedir"
          label="Home Directory"
          tabindex="4"
          :hint="
            mode == FormMode.READ ? '' : 'Path to the home directory within the virtual machine'
          "
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.homedir"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="shell"
          label="Shell"
          tabindex="5"
          :hint="mode == FormMode.READ ? '' : 'Path to the shell within the virtual machine'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.shell"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="pwcredential"
          label="Password"
          :tabindex="model.kind !== IdentityKind.PASSWORD ? -1 : 6"
          :type="isPwd ? 'password' : 'text'"
          :hint="mode == FormMode.READ ? '' : 'Enter the password for this identity'"
          :clearable="mode !== FormMode.READ"
          :disable="model.kind !== IdentityKind.PASSWORD"
          :readonly="mode == FormMode.READ"
          v-model="pwCredential"
        >
          <template v-slot:append>
            <q-icon
              :name="isPwd ? 'visibility_off' : 'visibility'"
              class="cursor-pointer"
              v-show="mode !== FormMode.READ"
              @click="isPwd = !isPwd"
            />
          </template>
        </q-input>
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="pubkeycredential"
          label="SSH Public Key"
          type="textarea"
          :tabindex="model.kind !== IdentityKind.PUBKEY ? -1 : 6"
          :hint="mode == FormMode.READ ? '' : 'Enter the SSH public key for this identity'"
          :clearable="mode != FormMode.READ"
          :disable="model.kind !== IdentityKind.PUBKEY"
          :readonly="mode == FormMode.READ"
          v-model="pubkeyCredential"
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
        color="primary"
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
