<script lang="ts" setup>
import { onMounted, ref } from "vue";
import { ConfigSchema, useConfigStore } from "@/store/config";

const store = useConfigStore();
const loading = ref(true);

onMounted(() => {
  store.get().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <q-page>
    <h1>Hello Quasar UI</h1>
    <p>Version of Kaso-Mashin: {{ store.config.version }}</p>
  </q-page>
</template>
