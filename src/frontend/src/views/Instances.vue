<script setup lang="ts">
import { onMounted } from "vue"
import { useInstancesStore } from "@/store/instances";
import InstanceCard from "@/components/InstanceCard.vue";

const instanceStore = useInstancesStore()

onMounted( () => {
  instanceStore.refresh()
})
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <InstanceCard v-for="instance in instanceStore.instances" :key="instance.instance_id" :instance="instance"/>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped>

</style>
