<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import InstanceCard from "@/components/InstanceCard.vue";
import { useInstancesStore } from "@/store/instances";

const router = useRouter();
const instancesStore = useInstancesStore();
const loading = ref(true);

async function onSelected(uid: string) {
  await router.push({ name: "InstanceDetail", params: { uid: uid } });
}

onMounted(() => {
  instancesStore.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <div class="row nowrap">
    <h4>Instances</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <InstanceCard
      v-for="instance in instancesStore.instances"
      :key="instance.uid"
      :instance="instance"
      @onSelected="onSelected"
    />

    <q-card class="km-new-card">
      <q-card-section class="absolute-center">
        <q-btn
          flat
          round
          color="primary"
          icon="add"
          :to="{ name: 'InstancesCreate' }"
        />
      </q-card-section>
    </q-card>
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>
