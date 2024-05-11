<script setup lang="ts">
import { NetworkGetSchema } from "@/store/networks";

defineProps<{
  network: NetworkGetSchema;
}>();
defineEmits<{
  (e: "onSelected", uid: string): void;
}>();
</script>

<template>
  <q-card
    v-ripple
    class="km-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', network.uid)">
    <q-card-section horizontal>
      <q-card-section class="q-pt-xs">
        <div class="text-caption text-weight-thin">{{ network.uid }}</div>
        <div class="text-h5 q-mt-sm q-mb-xs">{{ network.name }}</div>
      </q-card-section>
    </q-card-section>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">Kind</td>
          <td class="text-right">{{ network.kind }}</td>
        </tr>
        <tr>
          <td class="text-left">CIDR</td>
          <td class="text-right">{{ network.cidr }}</td>
        </tr>
        <tr>
          <td class="text-left">Gateway</td>
          <td class="text-right">{{ network.gateway }}</td>
        </tr>
        <tr>
          <td class="text-left">DHCP Range</td>
          <td class="text-right">
            {{ network.dhcp_start }} - {{ network.dhcp_end }}
          </td>
        </tr>
      </tbody>
    </q-markup-table>
  </q-card>
</template>
