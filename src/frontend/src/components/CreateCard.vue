<script setup lang="ts">
defineEmits<{
  (e: "onCreate"): void
}>();
</script>

<template>
  <q-card
    v-ripple
    class="km-entity-card cursor-pointer q-hoverable"
    @click="$emit('onCreate')">
    <q-card-section class="absolute-center">
      <q-btn
        fab
        color="primary"
        icon="add"
      />
    </q-card-section>
  </q-card>
</template>

<style scoped>
</style>
