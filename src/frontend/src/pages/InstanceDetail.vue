<script setup lang="ts">

import {onMounted, ref} from "vue";
import { useRoute } from 'vue-router'
import {useInstancesStore} from "@/store/instances";
import {InstanceGetSchema} from "@/store/instances";

const $route = useRoute()
const store = useInstancesStore()
const instance = ref({} as InstanceGetSchema)
const loading = ref(true)

onMounted( () => {
  store.get($route.params.uid).then( (i) => {
    instance.value = i
    loading.value = false
  })
})

</script>

<template>
 <p>Here is the instance detail: {{ instance.uid }}</p>
  <q-inner-loading :showing="loading">
    <q-spinner-gears size="50px" color="primary"/>
  </q-inner-loading>
</template>

<style scoped>

</style>
