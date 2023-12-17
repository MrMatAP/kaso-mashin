<script setup lang="ts">
import { ref } from 'vue'
import { Network } from '@/store/networks'

defineProps<{
    net: Network
}>()

let expand = ref()
</script>

<template>
  <v-card class="pa-2 ma-2">
    <template v-slot:title>{{ net.name }}</template>
    <template v-slot:subtitle>{{ net.kind }}: {{ net.network_id }}</template>
    <v-expand-transition>
      <div v-if="expand">
        <v-list class="bg-transparent" density="compact">
          <v-list-item title="Kind"><template v-slot:append>{{ net.kind }}</template></v-list-item>
            <v-list-item title="Netmask"><template v-slot:append>{{ net.nm4 }}</template></v-list-item>
            <v-list-item title="Gateway"><template v-slot:append>{{ net.gw4 }}</template></v-list-item>
            <v-list-item title="Nameserver"><template v-slot:append>{{ net.ns4 }}</template></v-list-item>
            <v-list-item title="DHCP4 Start"><template v-slot:append>{{ net.dhcp4_start }}</template></v-list-item>
            <v-list-item title="DHCP4 End"><template v-slot:append>{{ net.dhcp4_end }}</template></v-list-item>
            <v-list-item title="Host Interface"><template v-slot:append>{{ net.host_if }}</template></v-list-item>
            <v-list-item title="Host IPv4"><template v-slot:append>{{ net.host_ip4 }}</template></v-list-item>
            <v-list-item title="Host Phone Home Port"><template v-slot:append>{{ net.host_phone_home_port }}</template></v-list-item>
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
