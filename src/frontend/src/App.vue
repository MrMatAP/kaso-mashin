<script lang="ts" setup>
import { onMounted } from "vue";
import { useQuasar, useInterval } from "quasar";
import { useConfigStore } from "@/store/config";
import { useTaskStore } from "@/store/tasks";

import { useBootstrapStore } from "@/store/bootstraps";
import { useDiskStore } from "@/store/disks";
import { useIdentityStore } from "@/store/identities";
import { useImageStore } from "@/store/images";
import { useInstanceStore } from "@/store/instances";
import { useNetworkStore } from "@/store/networks";

const quasar = useQuasar();
const { registerInterval } = useInterval();
const configStore = useConfigStore();
const taskStore = useTaskStore();

const bootstrapStore = useBootstrapStore();
const diskStore = useDiskStore();
const identityStore = useIdentityStore();
const imageStore = useImageStore();
const instanceStore = useInstanceStore();
const networkStore = useNetworkStore();

onMounted(async () => {
  quasar.loading.show({
    delay: 400, // ms
    message: "Connecting to Kaso Mashin server...",
  });
  await configStore.get();
  await taskStore.list();
  registerInterval(async () => taskStore.list(), 3000);

  await bootstrapStore.list();
  //await diskStore.list();
  await identityStore.list();
  await imageStore.list();
  await instanceStore.list();
  await networkStore.list();

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

.detail-form
  max-width: 80%

.detail-form-button
  min-width: 200px

.detail-metadata
  margin-top: 100px
  max-width: 80%
</style>
