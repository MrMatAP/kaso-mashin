<script setup lang="ts">
import { ref } from 'vue'
import {ImageGetSchema} from "@/store/images";

defineProps<{
    image: ImageGetSchema
}>()

let expand = ref()
</script>

<template>
  <v-card class="pa-2 ma-2">
    <template v-slot:title>{{ image.name }}</template>
    <template v-slot:subtitle>{{ image.uid }}</template>
    <v-expand-transition>
      <div v-if="expand">
        <v-list class="bg-transparent" density="compact">
          <v-list-item :title="image.min_vcpu" subtitle="Minimum vCPU"/>
          <v-list-item :title="image.min_ram.value" subtitle="Minimum RAM"/>
          <v-list-item :title="image.min_disk.value" subtitle="Minimum Space"/>
        </v-list>
      </div>
    </v-expand-transition>
    <v-divider/>
    <v-card-actions>
      <v-btn @click="expand = !expand">
        {{ !expand ? 'Details' : 'Close' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>

</style>
