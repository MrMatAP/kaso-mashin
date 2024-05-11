<script setup lang="ts">
import { useImagesStore } from "@/store/images";
import ImageCard from "@/components/ImageCard.vue";
import { onMounted, ref } from "vue";

const store = useImagesStore();
const loading = ref(true);

onMounted(() => {
  store.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <ImageCard
          v-for="image in store.images"
          :key="image.uid"
          :image="image"
        />
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped></style>
