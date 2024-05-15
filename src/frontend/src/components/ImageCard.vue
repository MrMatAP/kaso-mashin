<script setup lang="ts">
import { ref } from 'vue'
import {Image} from "@/store/images";

defineProps<{
    image: Image
}>()

let expand = ref()
</script>

<template>
  <v-card class="pa-2 ma-2">
    <template v-slot:title>{{ image.name }}</template>
    <template v-slot:subtitle>{{ image.image_id }}</template>
    <v-expand-transition>
      <div v-if="expand">
        <v-list class="bg-transparent" density="compact">
          <v-list-item :title="image.min_cpu" subtitle="Minimum CPU"/>
          <v-list-item :title="image.min_ram" subtitle="Minimum RAM"/>
          <v-list-item :title="image.min_space" subtitle="Minimum Space"/>
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
