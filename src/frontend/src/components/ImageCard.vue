<script setup lang="ts">
import { ref } from "vue";
import { ImageGetSchema } from "@/store/images";

defineProps<{
  image: ImageGetSchema;
}>();
</script>

<template>
  <q-card class="km-card">
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
    <q-separator />
    <q-card-actions align="right">
      <q-btn flat>Modify</q-btn>
      <q-btn flat>Remove</q-btn>
    </q-card-actions>
  </q-card>
</template>
