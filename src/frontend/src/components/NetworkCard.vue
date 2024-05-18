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
    class="km-entity-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', network.uid)">
    <q-item>
      <q-item-section side>
        <q-avatar icon="settings_ethernet" size="lg" color="primary" text-color="white"/>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ network.name }}</q-item-label>
        <q-item-label caption>{{ network.uid }}</q-item-label>
      </q-item-section>
    </q-item>
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
