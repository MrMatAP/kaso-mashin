<script setup lang="ts">
defineProps<{
  title: string
}>()
defineSlots<{
  explanation: string
}>()
</script>

<template>
  <v-divider class="mt-4 mb-4"></v-divider>
  <v-sheet border rounded>
    <h2 class="text-h5 pa-2">{{ title }}</h2>
    <slot name="explanation"></slot>
  </v-sheet>
</template>

<style scoped>

</style>
