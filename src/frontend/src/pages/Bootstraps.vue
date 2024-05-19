<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useBootstrapStore } from "@/store/bootstraps";
import CreateCard from "@/components/CreateCard.vue";
import BootstrapCard from "@/components/BootstrapCard.vue";

const router = useRouter();
const bootstrapStore = useBootstrapStore();
const loading = ref(true);

async function onSelected(uid: string) {
  await router.push({ name: "BootstrapDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: 'BootstrapCreate' })
}

onMounted(() => {
  bootstrapStore.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <div class="row nowrap">
    <h4>Bootstraps</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <BootstrapCard
      v-for="bootstrap in bootstrapStore.bootstraps"
      :key="bootstrap.uid"
      :bootstrap="bootstrap"
      @onSelected="onSelected"
    />

    <CreateCard @onCreate="onCreate" />
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>

<style scoped>

</style>
