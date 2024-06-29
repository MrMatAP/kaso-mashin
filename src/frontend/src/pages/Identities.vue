<script setup lang="ts">
import { useRouter } from "vue-router";
import { useIdentityStore } from "@/store/identities";
import IdentityCard from "@/components/IdentityCard.vue";
import CreateCard from "@/components/CreateCard.vue";

const router = useRouter();
const identityStore = useIdentityStore();

async function onSelected(uid: string) {
  await router.push({ name: "IdentityDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: "IdentityCreate" });
}
</script>

<template>
  <div class="row nowrap">
    <h4>Identities</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <IdentityCard
      v-for="identity in identityStore.identities.values()"
      :key="identity.uid"
      :identity="identity"
      @onSelected="onSelected"
    />
    <CreateCard @onCreate="onCreate" />
  </div>
</template>
