<script setup lang="ts">
import { ref } from 'vue'
import { InstanceGetSchema } from '@/store/instances'

defineProps<{
    instance: InstanceGetSchema
}>()

let expand = ref()
</script>

<template>
  <v-card class="pa-2 ma-2">
    <template v-slot:title>{{ instance.name }}</template>
    <template v-slot:subtitle>{{ instance.uid }}</template>
    <v-expand-transition>
      <div v-if="expand">
        <v-list class="bg-transparent" density="compact">
          <v-list-item>
            <template v-slot:title>{{instance.mac}}</template>
            <template v-slot:subtitle>MAC</template>
          </v-list-item>
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
