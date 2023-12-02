<script setup lang="ts">
import {useNetworksStore} from "@/store/networks";
import NetworkCard from '@/components/NetworkCard.vue'

const store = useNetworksStore()
const networks = store.networks
</script>

<template>
  <v-form>
      <v-container>
          <v-row>
              <v-col cols="2" md="4">
                  <v-text-field label="Name" required></v-text-field>
                  <v-select label="Kind" :items="['Bridged', 'Host', 'Shared']"/>
              </v-col>
          </v-row>
          <v-row>

          </v-row>
      </v-container>
  </v-form>
  <v-container class="fill-height">
    <v-responsive class="fill-height">
      <v-row>
        <v-col v-for="net in networks">
          <NetworkCard :net="net"/>
        </v-col>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<style scoped>

</style>
