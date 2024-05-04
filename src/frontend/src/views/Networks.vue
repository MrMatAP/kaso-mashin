<script setup lang="ts">
import { onMounted } from 'vue'
import {useNetworksStore} from "@/store/networks";
import NetworkCard from '@/components/NetworkCard.vue'

const networksStore = useNetworksStore()

onMounted(() => {
  networksStore.list()
})
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <NetworkCard v-for="net in networksStore.networks" :key="net.uid" :net="net"/>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped>

</style>
