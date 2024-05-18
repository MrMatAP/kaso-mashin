<script setup lang="ts">
import { onMounted } from "vue";
import { useNetworkStore } from "@/store/networks";
import NetworkCard from "@/components/NetworkCard.vue";

const networksStore = useNetworkStore();

onMounted(() => {
  networksStore.list();
});
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <NetworkCard
          v-for="network in networksStore.networks"
          :key="network.uid"
          :network="network"
        />
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped></style>
