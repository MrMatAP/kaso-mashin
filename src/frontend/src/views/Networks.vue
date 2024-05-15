<script setup lang="ts">
import { onMounted } from 'vue'
import {useNetworksStore} from "@/store/networks";
import NetworkCard from '@/components/NetworkCard.vue'

const networksStore = useNetworksStore()

onMounted(() => {
  networksStore.refresh()
})
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <NetworkCard v-for="net in networksStore.networks" :key="net.network_id" :net="net"/>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped>

</style>
