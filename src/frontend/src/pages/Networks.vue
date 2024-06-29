<script setup lang="ts">
import { useRouter } from "vue-router";
import { useNetworkStore } from "@/store/networks";
import NetworkCard from "@/components/NetworkCard.vue";
import CreateCard from "@/components/CreateCard.vue";

const router = useRouter();
const networkStore = useNetworkStore();

async function onSelected(uid: string) {
  await router.push({ name: "NetworkDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: "NetworkCreate" });
}
</script>

<template>
  <div class="row nowrap">
    <h4>Networks</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <NetworkCard
      v-for="network in networkStore.networks.values()"
      :key="network.uid"
      :network="network"
      @onSelected="onSelected"
    />
    <CreateCard @onCreate="onCreate" />
  </div>
</template>
