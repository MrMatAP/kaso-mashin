<script setup lang="ts">
import { BootstrapGetSchema } from "@/store/bootstraps";

defineProps<{
  bootstrap: BootstrapGetSchema;
}>();
defineEmits<{
  (e: "onSelected", uid: string): void;
}>();
</script>

<template>
  <q-card
    v-ripple
    class="km-entity-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', bootstrap.uid)"
  >
    <q-item>
      <q-item-section side>
        <q-avatar icon="start" size="lg" color="primary" text-color="white"/>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ bootstrap.name }}</q-item-label>
        <q-item-label caption>{{ bootstrap.uid }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">Kind</td>
          <td class="text-right">{{ bootstrap.kind }}</td>
        </tr>
      </tbody>
    </q-markup-table>
  </q-card>
</template>
