<script setup lang="ts">
import NetworkCard from "@/components/NetworkCard.vue";
import {onMounted, ref} from "vue";
import {useNetworksStore} from "@/store/networks";

const store = useNetworksStore()
const loading = ref(true)

onMounted( () => {
  store.list().then( () => { loading.value = false })
})
</script>

<template>
  <div class="q-pa-md row items-start q-gutter-md">
    <NetworkCard v-for="network in store.networks" :key="network.uid" :network="network"/>

    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary"/>
    </q-inner-loading>
  </div>
</template>
