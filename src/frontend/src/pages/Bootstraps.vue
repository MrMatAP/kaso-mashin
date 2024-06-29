<script setup lang="ts">
import { useRouter } from "vue-router";
import { useBootstrapStore } from "@/store/bootstraps";
import CreateCard from "@/components/CreateCard.vue";
import BootstrapCard from "@/components/BootstrapCard.vue";

const router = useRouter();
const bootstrapStore = useBootstrapStore();

async function onSelected(uid: string) {
  await router.push({ name: "BootstrapDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: "BootstrapCreate" });
}
</script>

<template>
  <div class="row nowrap">
    <h4>Bootstraps</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <BootstrapCard
      v-for="bootstrap in bootstrapStore.bootstraps.values()"
      :key="bootstrap.uid"
      :bootstrap="bootstrap"
      @onSelected="onSelected"
    />
    <CreateCard @onCreate="onCreate" />
  </div>
</template>
