<script setup lang="ts">
import { useImagesStore } from "@/store/images";
import ImageCard from "@/components/ImageCard.vue";
import { onMounted, ref } from "vue";

const store = useImagesStore();
const loading = ref(true);

async function onAdd() {
  console.log("Will create new element");
}

onMounted(() => {
  store.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <div class="q-pa-md row items-start q-gutter-md">
    <ImageCard v-for="image in store.images" :key="image.uid" :image="image" />

    <q-card class="km-new-card" @click="onAdd">
      <q-card-section class="absolute-center">
        <q-btn flat round color="primary" icon="add" />
      </q-card-section>
    </q-card>
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>

<style lang="sass" scoped></style>
