<script setup lang="ts">

import {useImagesStore} from "@/store/images";

const imagesStore = useImagesStore()
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <v-col v-for="instance in instanceStore.instances">
          <InstanceCard :instance="instance"/>
        </v-col>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped>

</style>
