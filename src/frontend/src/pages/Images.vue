<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import ImageCard from "@/components/ImageCard.vue";
import { useImagesStore } from "@/store/images";

const router = useRouter();
const imagesStore = useImagesStore();
const loading = ref(true);

async function onSelected(uid: string) {
  await router.push({ name: "ImageDetail", params: { uid: uid } });
}

onMounted(() => {
  imagesStore.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <div class="row nowrap">
    <h4>Images</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <ImageCard
      v-for="image in imagesStore.images"
      :key="image.uid"
      :image="image"
      @onSelected="onSelected"
    />

    <q-card class="km-new-card">
      <q-card-section class="absolute-center">
        <q-btn
          flat
          round
          color="primary"
          icon="add"
          :to="{ name: 'ImagesCreate' }"
        />
      </q-card-section>
    </q-card>
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>

<style lang="sass" scoped></style>
