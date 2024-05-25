<script setup lang="ts">
import { InstanceGetSchema } from "@/store/instances";

defineProps<{
  instance: InstanceGetSchema;
}>();
defineEmits<{
  (e: "onSelected", uid: string): void;
}>();
</script>

<template>
  <q-card
    v-ripple
    class="km-entity-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', instance.uid)"
  >
    <q-item>
      <q-item-section side>
        <q-avatar icon="developer_board" size="lg" color="primary" text-color="white"/>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ instance.name }}</q-item-label>
        <q-item-label caption>{{ instance.uid }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">State</td>
          <td class="text-right">{{ instance.state }}</td>
        </tr>
        <tr>
          <td class="text-left">vCPUs</td>
          <td class="text-right">{{ instance.vcpu }}</td>
        </tr>
        <tr>
          <td class="text-left">RAM</td>
          <td class="text-right">{{ instance.ram.value }} {{ instance.ram.scale }}</td>
        </tr>
      </tbody>
    </q-markup-table>
  </q-card>
</template>
