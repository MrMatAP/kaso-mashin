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

const store = useIdentityStore();
const router = useRouter();
const route = useRoute();

const readonly: Ref<boolean> = ref(true);
const busy: Ref<boolean> = ref(false);
const pendingConfirmation: Ref<boolean> = ref(false);

const title: Ref<string> = ref("Identity Detail");
const pwCredential = ref("");
const pubkeyCredential = ref("");
const isPwd = ref(true);
const editForm = ref(null);

const uid: Ref<string> = ref("");
const original: Ref<IdentityGetSchema> = ref({} as IdentityGetSchema);
const model: Ref<
  IdentityGetSchema | IdentityCreateSchema | IdentityModifySchema
> = ref({} as IdentityCreateSchema);

async function onBack() {
  await router.push({ name: "Identities" });
}

async function onCancel() {
  if (model.value instanceof IdentityCreateSchema) {
    await onBack();
    return;
  }
  model.value = original.value;
  pubkeyCredential.value =
    model.value.kind === IdentityKind.PUBKEY ? model.value.credential : "";
  pwCredential.value =
    model.value.kind === IdentityKind.PASSWORD ? model.value.credential : "";
  title.value = "Identity: " + model.value.name;
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
  title.value = "Modify Identity: " + model.value.name;
  model.value = new IdentityModifySchema(original.value);
  pubkeyCredential.value =
    model.value.kind === IdentityKind.PUBKEY ? model.value.credential : "";
  pwCredential.value =
    model.value.kind === IdentityKind.PASSWORD ? model.value.credential : "";
  readonly.value = false;
}

async function onSubmit() {
  readonly.value = true;
  model.value.credential =
    model.value.kind === IdentityKind.PUBKEY
      ? pubkeyCredential.value
      : pwCredential.value;
  if (model.value instanceof IdentityCreateSchema) {
    store.create(model.value).then(() => {
      readonly.value = false;
      router.push({ name: "Identities" });
    });
  } else {
    store.modify(uid.value, model.value).then(() => {
      readonly.value = false;
      router.push({ name: "Identities" });
    });
  }
}

onMounted(async () => {
  if ("uid" in route.params) {
    // We're showing or editing an existing identity
    readonly.value = true;
    uid.value = route.params.uid as string;
    original.value = await store.get(uid.value);
    model.value = original.value;
    title.value = "Identity: " + model.value.name;
  } else {
    // We're creating a new identity
    readonly.value = false;
    model.value = new IdentityCreateSchema();
    title.value = "Create Identity";
  }
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
          :hint="readonly ? '' : 'A unique name for the identity'"
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.name"
        />
      </div>
      <div class="col-xs-12 col-sm-4 col-md-4 col-lg-4 col-xl-4">
        <q-select
          name="kind"
          label="Kind"
          tabindex="1"
          :hint="readonly ? '' : 'Kind of the identity credential'"
          :readonly="readonly"
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
          :hint="readonly ? '' : 'The display name of this identity'"
          :clearable="!readonly"
          :readonly="readonly"
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
            readonly
              ? ''
              : 'Path to the home directory within the virtual machine'
          "
          :clearable="!readonly"
          :readonly="readonly"
          v-model="model.homedir"
        />
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 col-xl-6">
        <q-input
          name="shell"
          label="Shell"
          tabindex="4"
          :hint="readonly ? '' : 'Path to the shell within the virtual machine'"
          :clearable="!readonly"
          :readonly="readonly"
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
          :hint="readonly ? '' : 'Enter the password for this identity'"
          :clearable="!readonly"
          :disable="model.kind !== IdentityKind.PASSWORD"
          :readonly="readonly"
          v-model="pwCredential"
        >
          <template v-slot:append>
            <q-icon
              :name="isPwd ? 'visibility_off' : 'visibility'"
              class="cursor-pointer"
              v-show="!readonly"
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
          :hint="readonly ? '' : 'Enter the SSH public key for this identity'"
          :clearable="!readonly"
          :disable="model.kind !== IdentityKind.PUBKEY"
          :readonly="readonly"
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
        :label="model instanceof IdentityCreateSchema ? 'Create' : 'Modify'"
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
