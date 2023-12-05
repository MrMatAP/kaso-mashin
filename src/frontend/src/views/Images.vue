<script setup lang="ts">
import { onMounted } from 'vue'
import { useImagesStore } from "@/store/images";

const imagesStore = useImagesStore()

onMounted( () => {
  imagesStore.refresh()
})
</script>

<template>
  <v-list>
    <v-list-item v-for="image in imagesStore.images">
      <v-list-item-title>{{ image.name }}</v-list-item-title>
      <v-list-item-subtitle>{{ image.image_id }}</v-list-item-subtitle>
    </v-list-item>
  </v-list>
</template>

<style scoped>

</style>
