<script setup lang="ts">
import { onMounted, ref, Ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { FormMode } from "@/base_types";
import {
  BootstrapCreateSchema,
  BootstrapGetSchema,
  BootstrapKind,
  BootstrapModifySchema,
  useBootstrapStore,
} from "@/store/bootstraps";

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
      return `Bootstrap: ${original.value.name}`;
    case FormMode.EDIT:
      return `Modify Bootstrap: ${original.value.name}`;
    case FormMode.CREATE:
      return "Create Bootstrap";
    default:
      return "Bootstrap Detail";
  }
});

const uid: Ref<string> = ref("");
const original: Ref<BootstrapGetSchema> = ref(new BootstrapGetSchema());
const model: Ref<any> = ref(new BootstrapGetSchema());

async function onBack() {
  await router.push({ name: "Bootstraps" });
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
  bootstrapStore.remove(uid.value).then(async () => {
    busy.value = false;
    await onBack();
  });
}

async function onEdit() {
  model.value = new BootstrapModifySchema(original.value);
  mode.value = FormMode.EDIT;
}

async function onSubmit() {
  busy.value = true;
  if (mode.value == FormMode.CREATE) {
    bootstrapStore.create(model.value).then(async () => {
      mode.value = FormMode.READ;
      busy.value = false;
      await onBack();
    });
  } else {
    bootstrapStore.modify(uid.value, model.value).then(async () => {
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
    original.value = await bootstrapStore.get(uid.value);
    model.value = original.value;
  } else {
    mode.value = FormMode.CREATE;
    model.value = new BootstrapCreateSchema();
  }
  busy.value = false;
});
</script>

<template>
  <q-dialog v-model="showRemoveConfirmationDialog" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm">Are you sure you want to remove this bootstrap?</span>
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
        <q-input name="uid" label="UID" readonly v-show="uid" :model-value="uid" />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-8 col-md-8 col-lg-8 col-xl-8">
        <q-input
          name="name"
          label="Name"
          tabindex="1"
          autofocus
          :hint="mode == FormMode.READ ? '' : 'A unique name for the bootstrap'"
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
          :hint="mode == FormMode.READ ? '' : 'Kind of the bootstrap'"
          :readonly="mode == FormMode.READ"
          :options="Object.values(BootstrapKind)"
          v-model="model.kind"
        />
      </div>
    </div>
    <div class="row q-col-gutter-x-md q-col-gutter-y-md">
      <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12">
        <q-input
          name="content"
          label="Bootstrap Content"
          tabindex="3"
          type="textarea"
          filled
          autograp
          :hint="mode == FormMode.READ ? '' : 'Bootstrap Content'"
          :clearable="mode !== FormMode.READ"
          :readonly="mode == FormMode.READ"
          v-model="model.content"
        />
      </div>
    </div>
    <div class="row q-gutter-xl justify-end">
      <q-btn
        class="detail-form-button"
        label="Edit"
        color="primary"
        tabindex="4"
        v-show="mode == FormMode.READ"
        @click="onEdit"
      />
      <q-btn
        class="detail-form-button"
        label="Remove"
        color="negative"
        tabindex="5"
        v-show="mode == FormMode.READ"
        @click="showRemoveConfirmationDialog = true"
      />
      <q-btn
        class="detail-form-button"
        label="Cancel"
        color="primary"
        tabindex="6"
        v-show="mode !== FormMode.READ"
        @click="onCancel"
      />
      <q-btn
        class="detail-form-button"
        :label="mode == FormMode.CREATE ? 'Create' : 'Modify'"
        type="submit"
        color="positive"
        tabindex="7"
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
        <td class="text-left"><b>Required Keys</b></td>
        <td class="text-left">
          <q-list dense>
            <q-item v-for="key in model.required_keys">
              <q-item-section side left>
                <q-icon name="note" />
              </q-item-section>
              <q-item-section>{{ key }}</q-item-section>
            </q-item>
          </q-list>
        </td>
      </tr>
    </tbody>
  </q-markup-table>
</template>
