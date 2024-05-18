<script lang="ts" setup>
import { onMounted } from "vue";
import { useQuasar } from "quasar";
import { useConfigStore } from "@/store/config";

const store = useConfigStore();
const $q = useQuasar();

onMounted(() => {
  $q.loading.show({
    delay: 400, // ms
    message: "Connecting to Kaso Mashin server...",
  });
  store.get().then(() => {
    $q.loading.hide();
  });
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
