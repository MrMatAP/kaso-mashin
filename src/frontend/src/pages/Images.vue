<script setup lang="ts">
import { useRouter } from "vue-router";
import { useImageStore } from "@/store/images";
import ImageCard from "@/components/ImageCard.vue";
import CreateCard from "@/components/CreateCard.vue";
import ImagePending from "@/components/ImagePending.vue";

const router = useRouter();
const imageStore = useImageStore();

async function onSelected(uid: string) {
  await router.push({ name: "ImageDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: "ImageCreate" });
}
</script>

<template>
  <div class="row nowrap">
    <h4>Images</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <ImageCard
      v-for="image in imageStore.images.values()"
      :key="image.uid"
      :image="image"
      @onSelected="onSelected"
    />
    <ImagePending
      v-for="[taskUid, image] in imageStore.pendingImages"
      :taskUid="taskUid"
      :image="image"
    />
    <CreateCard @onCreate="onCreate" />
  </div>
</template>
