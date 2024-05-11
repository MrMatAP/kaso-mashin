<script setup lang="ts">
import InstanceCard from "@/components/InstanceCard.vue";
import InstanceDetail from "@components/InstanceDetail.vue";
import { onMounted, ref } from "vue";
import { useInstancesStore } from "@/store/instances";

const store = useInstancesStore();
const loading = ref(true);

onMounted(() => {
  store.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <div class="q-pa-md row items-start q-gutter-md">
    <InstanceCard
      v-for="instance in store.instances"
      :key="instance.uid"
      :instance="instance"
    />

    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>
