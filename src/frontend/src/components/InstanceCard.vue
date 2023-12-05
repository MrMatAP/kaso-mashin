<script setup lang="ts">
import { ref } from 'vue'
import { Instance } from '@/store/instances'

defineProps<{
    instance: Instance
}>()

let expand = ref()
</script>

<template>
  <v-card class="pa-2 ma-2">
    <template v-slot:title>{{ instance.name }}</template>
    <template v-slot:subtitle>{{ instance.instance_id }}</template>
    <v-expand-transition>
      <div v-if="expand">
        <v-list class="bg-transparent" density="compact">
          <v-list-item title="MAC"><template v-slot:append>{{ instance.mac }}</template></v-list-item>
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
