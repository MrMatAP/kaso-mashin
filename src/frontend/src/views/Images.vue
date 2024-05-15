<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Image, useImagesStore } from "@/store/images";
import ExplanationNote from "@/components/ExplanationNote.vue";
import ImageDialog from "@/components/ImageDialog.vue";
import {DialogKind} from "@/constants";

const imagesStore = useImagesStore()
const loading = ref(true)

const headers = [
  {
    key: 'image_id',
    title: 'Image Id',
    sortable: true
  },
  {
    key: 'name',
    title: 'Name',
    sortable: true
  },
  {
    key: 'path',
    title: 'Path'
  },
  {
    key: 'min_cpu',
    title: 'Minimal CPUs',
  },
  {
    key: 'min_ram',
    title: 'Minimal RAM'
  },
  {
    key: 'min_space',
    title: 'Minimal Space'
  },
  {
    key: 'actions',
    title: 'Actions',
    sortable: false
  }
]

function createImage(image: Image) {
  loading.value = true
  imagesStore.create(image).then( () => {
    imagesStore.refresh()
    loading.value = false
  })
}

function modifyImage(image: Image) {
  loading.value = true
  imagesStore.modify(image).then( () => {
    imagesStore.refresh()
    loading.value = false
  })
}

function removeImage(image: Image) {
  loading.value = true
  imagesStore.remove(image).then( () => {
    imagesStore.refresh()
    loading.value = false
  })
}

onMounted( () => {
  imagesStore.refresh().then( () => { loading.value = false })
})
</script>

<template>
  <v-container>
    <v-data-table
      :headers="headers"
      :items="imagesStore.images"
      :loading="loading"
      :sort-by="[{ key: 'image_id', order: 'asc'}]">
      <template v-slot:top>
        <v-toolbar>
          <v-toolbar-title>Images</v-toolbar-title>
          <v-divider class="mx-4" :inset="true" :vertical="true"></v-divider>
          <v-spacer></v-spacer>
          <v-btn color="primary" dark class="mb-2">
            Create Image
            <image-dialog :kind="DialogKind.create" :predefined="imagesStore.predefined_images" @accept="createImage"/>
          </v-btn>
        </v-toolbar>
      </template>
      <template v-slot:[`item.actions`]="{item}">
        <v-btn density="compact" :rounded="true" variant="plain">
          <v-icon size="small">mdi-pencil</v-icon>
          <image-dialog :kind="DialogKind.modify" :input="item" :predefined="imagesStore.predefined_images" @accept="modifyImage"/>
        </v-btn>
        <v-btn density="compact" :rounded="true" variant="plain">
          <v-icon size="small">mdi-delete</v-icon>
          <image-dialog :kind="DialogKind.remove" :input="item" :predefined="imagesStore.predefined_images" @accept="removeImage"/>
        </v-btn>
      </template>
      <template v-slot:loading>
        <v-skeleton-loader type="table-row@10"></v-skeleton-loader>
      </template>
    </v-data-table>
    <explanation-note title="Images">
      <template v-slot:explanation>
        <p class="text-body-2 pa-4">
          Images are the OS disks from which your virtual machines run. You can download from a set
          of predefined images OS vendors offer or upload your own.
        </p>
        <p class="text-body-2 pa-4">
          Do not delete images that are in use. They are the backing stores of your virtual machines.
        </p>
      </template>
    </explanation-note>
  </v-container>
</template>

<style scoped>

</style>
