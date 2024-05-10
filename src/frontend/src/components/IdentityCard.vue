<script setup lang="ts">
import {IdentityGetSchema} from "@/store/identities";

defineProps<{
    identity: IdentityGetSchema
}>()
defineEmits<{
  (e: 'onSelected', uid: string): void
}>()
</script>

<template>
  <q-card v-ripple class="km-card cursor-pointer q-hoverable" @click="$emit('onSelected', identity.uid)">
    <q-card-section horizontal>
      <q-card-section class="q-pt-xs">
        <div class="text-caption text-weight-thin">{{ identity.uid }}</div>
        <div class="text-h5 q-mt-sm q-mb-xs">{{ identity.name }}</div>
      </q-card-section>
    </q-card-section>
    <q-separator/>
    <q-markup-table>
      <tbody>
      <tr><td class="text-left">Kind</td><td class="text-right">{{ identity.kind }}</td></tr>
      <tr><td class="text-left">GECOS</td><td class="text-right">{{ identity.gecos }}</td></tr>
      <tr><td class="text-left">Home Directory</td><td class="text-right">{{ identity.homedir }}</td></tr>
      <tr><td class="text-left">Shell</td><td class="text-right">{{ identity.shell }}</td></tr>
      </tbody>
    </q-markup-table>
  </q-card>
</template>
