<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useImageStore } from "@/store/images";
import ImageCard from "@/components/ImageCard.vue";
import CreateCard from "@/components/CreateCard.vue";
import ImagePending from "@/components/ImagePending.vue";

const router = useRouter();
const imageStore = useImageStore();
const loading = ref(true);

async function onSelected(uid: string) {
  await router.push({ name: "ImageDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: 'ImageCreate' });
}

onMounted(() => {
  imageStore.list().then(() => {
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
      v-for="image in imageStore.images"
      :key="image.uid"
      :image="image"
      @onSelected="onSelected"
    />
    <ImagePending
      v-for="[taskUid, image] in imageStore.pendingImages"
      :taskUid="taskUid"
      :image="image"/>

    <CreateCard @onCreate="onCreate"/>
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>
