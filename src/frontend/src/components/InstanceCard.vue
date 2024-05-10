<script setup lang="ts">
import { ref } from 'vue'
import { InstanceGetSchema } from '@/store/instances'
import {IdentityModifySchema} from "@/store/identities";

defineProps<{
    instance: InstanceGetSchema
}>()
const emits = defineEmits<{
  (e: 'details'): void,
  (e: 'modify', output: IdentityModifySchema): void,
  (e: 'cancel'): void
}>()

async function onDetails(e) {
  emit('')
}
</script>

<template>
  <q-card class="km-card">
    <q-card-section horizontal>
      <q-card-section class="q-pt-xs">
        <div class="text-caption text-weight-thin">{{ instance.uid }}</div>
        <div class="text-h5 q-mt-sm q-mb-xs">{{ instance.name }}</div>
      </q-card-section>
    </q-card-section>
    <q-separator/>
    <q-markup-table>
      <tbody>
      <tr><td class="text-left">MAC</td><td class="text-right">{{ instance.mac }}</td></tr>
      </tbody>
    </q-markup-table>
    <q-separator/>
    <q-card-actions align="right">
      <q-btn flat @click="onDetails">Details</q-btn>
      <q-btn flat @click="onModify">Modify</q-btn>
      <q-btn flat @click="onRemove">Remove</q-btn>
    </q-card-actions>
  </q-card>
</template>
