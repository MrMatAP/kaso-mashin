<script setup lang="ts">
import { ImageGetSchema } from "@/store/images";

defineProps<{
  image: ImageGetSchema;
}>();
defineEmits<{
  (e: "onSelected", uid: string): void;
}>();
</script>

<template>
  <q-card
    v-ripple
    class="km-entity-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', image.uid)"
  >
    <q-item>
      <q-item-section side>
        <q-avatar icon="work_outline" size="lg" color="primary" text-color="white"/>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ image.name }}</q-item-label>
        <q-item-label caption>{{ image.uid }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">Minimum vCPU</td>
          <td class="text-right">{{ image.min_vcpu }}</td>
        </tr>
        <tr>
          <td class="text-left">Minimum RAM</td>
          <td class="text-right">{{ image.min_ram.value }}</td>
        </tr>
        <tr>
          <td class="text-left">Minimum Disk Space</td>
          <td class="text-right">{{ image.min_disk.value }}</td>
        </tr>
      </tbody>
    </q-markup-table>
  </q-card>
</template>
