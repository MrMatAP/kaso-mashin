<script setup lang="ts">
import { ref } from 'vue'
import {NetworkGetSchema} from '@/store/networks'

defineProps<{
    net: NetworkGetSchema
}>()

let expand = ref()
</script>

<template>
  <v-card class="pa-2 ma-2">
    <template v-slot:title>{{ net.name }}</template>
    <template v-slot:subtitle>{{ net.kind }}: {{ net.uid }}</template>
    <v-expand-transition>
      <div v-if="expand">
        <v-list class="bg-transparent" density="compact">
          <v-list-item title="Kind"><template v-slot:append>{{ net.kind }}</template></v-list-item>
            <v-list-item title="CIDR"><template v-slot:append>{{ net.cidr }}</template></v-list-item>
            <v-list-item title="Gateway"><template v-slot:append>{{ net.gateway }}</template></v-list-item>
            <v-list-item title="DHCP4 Start"><template v-slot:append>{{ net.dhcp_start }}</template></v-list-item>
        </v-list>
      </div>
    </v-expand-transition>
    <v-divider/>
    <v-card-actions>
      <v-btn @click="expand = !expand">
        {{ !expand ? 'Details' : 'Close' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>

</style>
