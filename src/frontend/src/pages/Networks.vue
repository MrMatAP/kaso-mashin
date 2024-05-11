<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import NetworkCard from "@/components/NetworkCard.vue";
import { useNetworksStore } from "@/store/networks";

const router = useRouter();
const store = useNetworksStore();
const loading = ref(true);

async function onSelected(uid: string) {
  await router.push({ name: "IdentityDetail", params: { uid: uid } });
}

onMounted(() => {
  store.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <div class="row nowrap">
    <h4>Networks</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <NetworkCard
      v-for="network in store.networks"
      :key="network.uid"
      :network="network"
      @onSelected="onSelected"
    />

    <q-card class="km-new-card">
      <q-card-section class="absolute-center">
        <q-btn
          flat
          round
          color="primary"
          icon="add"
          :to="{ name: 'NetworksCreate' }"
        />
      </q-card-section>
    </q-card>
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>
