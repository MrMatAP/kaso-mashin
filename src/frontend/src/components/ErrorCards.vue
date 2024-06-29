<script setup lang="ts">
import { useErrorStore } from "@/store/errors";

const errorStore = useErrorStore();
</script>

<template>
  <q-card flat bordered v-for="error in errorStore.errors">
    <q-item>
      <q-item-section avatar>
        <q-avatar color="negative" text-color="white" icon="error" />
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ error.msg }}</q-item-label>
      </q-item-section>
      <q-item-section side>
        <q-item-label caption>Side</q-item-label>
      </q-item-section>
    </q-item>
  </q-card>
</template>

<style scoped></style>
