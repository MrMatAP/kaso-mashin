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

const instancesStore = useInstanceStore();
const tasksStore = useTaskStore();
const router = useRouter();
const route = useRoute();

const readonly: Ref<boolean> = ref(true);
const busy: Ref<boolean> = ref(false);
const pendingConfirmation: Ref<boolean> = ref(false);

const title: Ref<string> = ref("Instance Detail");
const editForm = ref(null);
const empty = ref("");

const uid: Ref<string> = ref("");
const original: Ref<InstanceGetSchema> = ref({} as InstanceGetSchema);
const model: Ref<
  InstanceGetSchema | InstanceCreateSchema | InstanceModifySchema
> = ref(new InstanceCreateSchema());
const viewModel: Ref<InstanceGetSchema> = ref(new InstanceGetSchema())
const editModel: Ref<InstanceModifySchema> = ref(new InstanceModifySchema(viewModel.value))
const createModel: Ref<InstanceCreateSchema> = ref(new InstanceCreateSchema())

async function onBack() {
  await router.push({ name: "Instances" });
}

async function onCancel() {
  if (model.value instanceof InstanceCreateSchema) {
    await onBack();
    return;
  }
  model.value = original.value;
  title.value = "Instance: " + model.value.name;
  readonly.value = true;
}

async function onRemove() {
  busy.value = true;
  instancesStore.remove(uid.value).then(() => {
    busy.value = false;
    onBack();
  });
}

async function onEdit() {
  title.value = "Modify Instance: " + model.value.name;
  model.value = new InstanceModifySchema(original.value);
  readonly.value = false;
}

async function onSubmit() {
  readonly.value = true;
  if (model.value instanceof InstanceCreateSchema) {
    instancesStore.create(model.value).then((task) => {
      readonly.value = false;
      console.dir(task);
      onBack();
    });
  } else {
    instancesStore.modify(uid.value, model.value).then(() => {
      readonly.value = false;
      onBack();
    });
  }
}

onMounted(async () => {
  if ("uid" in route.params) {
    // We're showing or editing an existing instance
    readonly.value = true;
    uid.value = route.params.uid as string;
    original.value = await instancesStore.get(uid.value);
    model.value = original.value;
    title.value = "Instance: " + model.value.name;
  } else {
    // We're creating a new instance
    readonly.value = false;
    model.value = new InstanceCreateSchema();
    title.value = "Create Instance";
  }
});
</script>

<template>
  <q-dialog v-model="pendingConfirmation" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm"
          >Are you sure you want to remove this instance?</span
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
          :hint="readonly ? '' : 'A unique name for the instance'"
          :clearable="!readonly"
          :readonly="readonly"
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
          :hint="readonly ? '' : 'The instance path on local disk'"
          :clearable="!readonly"
          :readonly="readonly"
          v-show="model instanceof InstanceGetSchema"
          v-model="viewModel.path"
        />
        <!-- TODO -->
        <!--          v-model="model instanceof InstanceGetSchema ? model.path : empty"-->
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
        :label="model instanceof InstanceCreateSchema ? 'Create' : 'Modify'"
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
