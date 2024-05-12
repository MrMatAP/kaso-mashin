<script setup lang="ts">
import { InstanceGetSchema } from "@/store/instances";

defineProps<{
  instance: InstanceGetSchema;
}>();
const emits = defineEmits<{
  (e: "onSelected", uid: string): void;
}>();
</script>

<template>
  <q-card
    v-ripple
    class="km-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', instance.uid)"
  >
    <q-card-section horizontal>
      <q-card-section class="q-pt-xs">
        <div class="text-caption text-weight-thin">{{ instance.uid }}</div>
        <div class="text-h5 q-mt-sm q-mb-xs">{{ instance.name }}</div>
      </q-card-section>
    </q-card-section>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">MAC</td>
          <td class="text-right">{{ instance.mac }}</td>
        </tr>
      </tbody>
    </q-markup-table>
  </q-card>
</template>
