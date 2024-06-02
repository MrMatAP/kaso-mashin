<script lang="ts" setup>
import { onMounted } from "vue";
import { useQuasar, useInterval } from "quasar";
import { useConfigStore } from "@/store/config";
import { useTaskStore } from "@/store/tasks";
import { useNetworkStore } from "@/store/networks";
import { useImageStore } from "@/store/images";
import { useBootstrapStore } from "@/store/bootstraps";
import { useErrorStore, ErrorSchema } from "@/store/errors";

const quasar = useQuasar();
const { registerInterval } = useInterval();
const configStore = useConfigStore();
const taskStore = useTaskStore();
const networkStore = useNetworkStore();
const imageStore = useImageStore();
const bootstrapStore = useBootstrapStore();
const errorStore = useErrorStore();

onMounted(async () => {
  quasar.loading.show({
    delay: 400, // ms
    message: "Connecting to Kaso Mashin server...",
  });
  await configStore.get();
  await networkStore.list();
  await imageStore.list();
  await bootstrapStore.list();
  await taskStore.list();

  registerInterval(async () => taskStore.list(), 3000);

  errorStore.errors.push(new ErrorSchema());
  errorStore.errors.push(new ErrorSchema());
  quasar.loading.hide();
});
</script>

<template>
  <router-view />
</template>

<style lang="sass">
.km-entity-card
  min-width: 320px
  min-height: 277px
</style>
