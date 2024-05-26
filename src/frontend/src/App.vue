<script lang="ts" setup>
import { onMounted } from "vue";
import { useQuasar } from "quasar";
import { useConfigStore } from "@/store/config";
import { useTaskStore } from '@/store/tasks';
import { useNetworkStore } from "@/store/networks";
import { useImageStore } from '@/store/images';
import { useBootstrapStore } from "@/store/bootstraps";

const quasar = useQuasar();
const configStore = useConfigStore();
const taskStore = useTaskStore();
const networkStore = useNetworkStore();
const imageStore = useImageStore();
const bootstrapStore = useBootstrapStore();

onMounted(async () => {
  quasar.loading.show({
    delay: 400, // ms
    message: "Connecting to Kaso Mashin server...",
  });
  await configStore.get()
  await networkStore.list()
  await imageStore.list()
  await bootstrapStore.list()

  const taskSocket = new WebSocket('ws://localhost:3000/api/tasks/notify')
  taskSocket.onopen = (evt) => { console.dir(evt) }
  taskSocket.onerror = (evt) => { console.dir(evt) }
  taskSocket.onclose = (evt) => { console.dir(evt)}
  taskSocket.onmessage = (evt) => { console.dir(evt) }

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
