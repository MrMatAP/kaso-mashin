<script setup lang="ts">

import {useImagesStore} from "@/store/images";
import ImageCard from "@/components/ImageCard.vue";

const imagesStore = useImagesStore()
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <ImageCard v-for="image in imagesStore.images" :key="image.image_id" :image="image"/>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped>

</style>
