<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useInstanceStore } from "@/store/instances";
import InstanceCard from "@/components/InstanceCard.vue";
import CreateCard from "@/components/CreateCard.vue";

const router = useRouter();
const instanceStore = useInstanceStore();
const loading = ref(true);

async function onSelected(uid: string) {
  await router.push({ name: "InstanceDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: 'InstanceCreate' })
}

onMounted(() => {
  instanceStore.list().then(() => {
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
      v-for="instance in instanceStore.instances"
      :key="instance.uid"
      :instance="instance"
      @onSelected="onSelected"
    />

    <CreateCard @onCreate="onCreate" />
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>
