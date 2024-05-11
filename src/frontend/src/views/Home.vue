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
  <v-container class="fill-height">
    <v-responsive class="align-center text-center fill-height">
      <p>Main Content goes here</p>
      <p>{{ store.config.version }}</p>
    </v-responsive>
  </v-container>
</template>
