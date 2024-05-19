<script setup lang="ts">
import { onMounted, ref, Ref } from "vue";
import { useRoute, useRouter } from "vue-router";
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

const readMode: Ref<boolean> = ref(true);
const modifyMode: Ref<boolean> = ref(false);
const createMode: Ref<boolean> = ref(false);
const busy: Ref<boolean> = ref(false);
const pendingConfirmation: Ref<boolean> = ref(false);
const editForm = ref(null);

const title: Ref<string> = ref("Identity Detail");
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
  if (createMode.value) {
    createMode.value = false;
    await onBack();
    return;
  }
  model.value = original.value;
  pubkeyCredential.value =
    model.value.kind === IdentityKind.PUBKEY ? model.value.credential : "";
  pwCredential.value =
    model.value.kind === IdentityKind.PASSWORD ? model.value.credential : "";
  title.value = "Identity: " + model.value.name;
  readMode.value = true;
  modifyMode.value = true;
}

async function onRemove() {
  busy.value = true;
  identityStore.remove(uid.value).then(() => {
    busy.value = false;
    onBack();
  });
}

async function onEdit() {
  title.value = "Modify Identity: " + model.value.name;
  model.value = new IdentityModifySchema(original.value);
  pubkeyCredential.value =
    model.value.kind === IdentityKind.PUBKEY ? model.value.credential : "";
  pwCredential.value =
    model.value.kind === IdentityKind.PASSWORD ? model.value.credential : "";
  readMode.value = false;
  modifyMode.value = false;
}

async function onSubmit() {
  readMode.value = true;
  model.value.credential =
    model.value.kind === IdentityKind.PUBKEY
      ? pubkeyCredential.value
      : pwCredential.value;
  if (model.value instanceof IdentityCreateSchema) {
    identityStore.create(model.value).then(async () => {
      readMode.value = false;
      await onBack();
    });
  } else {
    identityStore.modify(uid.value, model.value).then(async () => {
      readMode.value = false;
      await onBack();
    });
  }
}

onMounted(async () => {
  busy.value = true;
  if ("uid" in route.params) {
    // We're showing or editing an existing identity
    readMode.value = true;
    modifyMode.value = true;
    createMode.value = true;
    uid.value = route.params.uid as string;
    original.value = await identityStore.get(uid.value);
    model.value = original.value;
    title.value = "Identity: " + model.value.name;
  } else {
    // We're creating a new identity
    readMode.value = false;
    modifyMode.value = false;
    createMode.value = false;
    model.value = new IdentityCreateSchema();
    title.value = "Create Identity";
  }
  busy.value = false;
});
</script>

<template>
  <q-dialog v-model="pendingConfirmation" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm"
          >Are you sure you want to remove this identity?</span
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
          :hint="readMode ? '' : 'A unique name for the identity'"
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
          :hint="readMode ? '' : 'Identity Kind'"
          :readonly="readMode"
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
          tabindex="2"
          :hint="readMode ? '' : 'The display name of this identity'"
          :clearable="modifyMode || createMode"
          :readonly="readMode"
          v-model="model.gecos"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="homedir"
          label="Home Directory"
          tabindex="3"
          :hint="
            readMode
              ? ''
              : 'Path to the home directory within the virtual machine'
          "
          :clearable="!readMode"
          :readonly="readMode"
          v-model="model.homedir"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="shell"
          label="Shell"
          tabindex="4"
          :hint="readMode ? '' : 'Path to the shell within the virtual machine'"
          :clearable="!readMode"
          :readonly="readMode"
          v-model="model.shell"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="pwcredential"
          label="Password"
          :tabindex="model.kind !== IdentityKind.PASSWORD ? 99 : 5"
          :type="isPwd ? 'password' : 'text'"
          :hint="readMode ? '' : 'Enter the password for this identity'"
          :clearable="!readMode"
          :disable="model.kind !== IdentityKind.PASSWORD"
          :readonly="readMode"
          v-model="pwCredential"
        >
          <template v-slot:append>
            <q-icon
              :name="isPwd ? 'visibility_off' : 'visibility'"
              class="cursor-pointer"
              v-show="!readMode"
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
          :tabindex="model.kind !== IdentityKind.PUBKEY ? 99 : 5"
          :hint="readMode ? '' : 'Enter the SSH public key for this identity'"
          :clearable="!readMode"
          :disable="model.kind !== IdentityKind.PUBKEY"
          :readonly="readMode"
          v-model="pubkeyCredential"
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
