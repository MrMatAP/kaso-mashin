<script setup lang="ts">
import { ref } from 'vue'
import { NetworkGetSchema } from "@/store/networks";

defineProps<{
    network: NetworkGetSchema
}>()
</script>

<template>
  <q-card class="km-card">
    <q-card-section horizontal>
      <q-card-section class="q-pt-xs">
        <div class="text-caption text-weight-thin">{{ network.uid }}</div>
        <div class="text-h5 q-mt-sm q-mb-xs">{{ network.name }}</div>
      </q-card-section>
    </q-card-section>
    <q-separator/>
    <q-markup-table>
      <tbody>
        <tr><td class="text-left">Kind</td><td class="text-right">{{ network.kind }}</td></tr>
        <tr><td class="text-left">CIDR</td><td class="text-right">{{ network.cidr }}</td></tr>
        <tr><td class="text-left">Gateway</td><td class="text-right">{{ network.gateway }}</td></tr>
        <tr><td class="text-left">DHCP Range</td><td class="text-right">{{ network.dhcp_start }} - {{ network.dhcp_end }}</td></tr>
      </tbody>
    </q-markup-table>
    <q-separator/>
    <q-card-actions align="right">
      <q-btn flat>Modify</q-btn>
      <q-btn flat>Remove</q-btn>
    </q-card-actions>
  </q-card>
</template>
