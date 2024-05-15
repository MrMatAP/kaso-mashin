<script setup lang="ts">

</script>

<template>
  <v-navigation-drawer>
    <v-list>
      <v-list-item :to="{ name: 'Instances' }">Instances</v-list-item>
      <v-list-item :to="{ name: 'Identities' }">Identities</v-list-item>
      <v-list-item :to="{ name: 'Networks' }">Networks</v-list-item>
      <v-list-item :to="{ name: 'Images' }">Images</v-list-item>
      <v-list-item :to="{ name: 'Images-Grid'}">Images (Grid)</v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>

<style scoped>

</style>
