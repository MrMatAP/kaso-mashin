<script setup lang="ts">
defineProps<{
  pending: boolean,
  entityName: string
}>();
defineEmits<{
  (e: "onRemove"): void
}>();
</script>

<template>
  <q-dialog v-show="pending" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <span class="q-ml-sm">Are you sure you want to remove this {{ entityName }}?</span>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="Cancel" color="primary" v-close-popup />
        <q-btn
          flat
          label="Remove"
          color="primary"
          v-close-popup
          @click="$emit('onRemove')"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<style scoped>

</style>
