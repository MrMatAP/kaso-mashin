<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useInstanceStore } from "@/store/instances";
import InstanceCard from "@/components/InstanceCard.vue";

const store = useInstanceStore();
const loading = ref(true);

onMounted(() => {
  store.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <InstanceCard
          v-for="instance in store.instances"
          :key="instance.uid"
          :instance="instance"
        />
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped></style>
