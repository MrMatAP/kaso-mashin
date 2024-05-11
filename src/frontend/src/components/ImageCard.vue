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
    class="km-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', image.uid)"
  >
    <q-card-section horizontal>
      <q-card-section class="q-pt-xs">
        <div class="text-caption text-weight-thin">{{ image.uid }}</div>
        <div class="text-h5 q-mt-sm q-mb-xs">{{ image.name }}</div>
      </q-card-section>
    </q-card-section>
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
