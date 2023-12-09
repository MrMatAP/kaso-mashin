<script setup lang="ts">
import { onMounted } from "vue";
import { useIdentitiesStore } from "@/store/identities";

const identitiesStore = useIdentitiesStore()

onMounted( () => {
  identitiesStore.refresh()
})
</script>

<template>
  <v-list>
    <v-list-item v-for="identity in identitiesStore.identities">
      <v-list-item-title>{{ identity.name }}</v-list-item-title>
      <v-list-item-subtitle>{{ identity.identity_id }}</v-list-item-subtitle>
    </v-list-item>
  </v-list>
</template>

<style scoped>

</style>
