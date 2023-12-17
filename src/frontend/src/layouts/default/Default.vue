<template>
  <v-app class="rounded rounded-md">
    <default-bar />
    <default-nav />
    <default-view />
  </v-app>
</template>

<script lang="ts" setup>
  import DefaultBar from './AppBar.vue'
  import DefaultNav from './AppNav.vue'
  import DefaultView from './View.vue'
</script>
