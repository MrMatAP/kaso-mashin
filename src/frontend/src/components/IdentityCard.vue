<script setup lang="ts">
import { IdentityGetSchema } from "@/store/identities";

defineProps<{
  identity: IdentityGetSchema;
}>();
defineEmits<{
  (e: "onSelected", uid: string): void;
}>();
</script>

<template>
  <q-card
    v-ripple
    class="km-entity-card cursor-pointer q-hoverable"
    @click="$emit('onSelected', identity.uid)"
  >
    <q-item>
      <q-item-section side>
        <q-avatar icon="fingerprint" size="lg" color="primary" text-color="white"/>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ identity.name }}</q-item-label>
        <q-item-label caption>{{ identity.uid }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">Kind</td>
          <td class="text-right">{{ identity.kind }}</td>
        </tr>
        <tr>
          <td class="text-left">GECOS</td>
          <td class="text-right">{{ identity.gecos }}</td>
        </tr>
        <tr>
          <td class="text-left">Home Directory</td>
          <td class="text-right">{{ identity.homedir }}</td>
        </tr>
        <tr>
          <td class="text-left">Shell</td>
          <td class="text-right">{{ identity.shell }}</td>
        </tr>
      </tbody>
    </q-markup-table>
  </q-card>
</template>
