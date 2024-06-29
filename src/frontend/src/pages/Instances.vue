<script setup lang="ts">
import { useRouter } from "vue-router";
import { useInstanceStore } from "@/store/instances";
import InstanceCard from "@/components/InstanceCard.vue";
import CreateCard from "@/components/CreateCard.vue";
import InstancePending from "@/components/InstancePending.vue";

const router = useRouter();
const instanceStore = useInstanceStore();

async function onSelected(uid: string) {
  await router.push({ name: "InstanceDetail", params: { uid: uid } });
}

async function onCreate() {
  await router.push({ name: "InstanceCreate" });
}
</script>

<template>
  <div class="row nowrap">
    <h4>Instances</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <InstanceCard
      v-for="instance in instanceStore.instances.values()"
      :key="instance.uid"
      :instance="instance"
      @onSelected="onSelected"
    />
    <InstancePending
      v-for="[taskUid, instance] in instanceStore.pendingInstances"
      v-bind:key="taskUid"
      :taskUid="taskUid"
      :instance="instance"
    />
    <CreateCard @onCreate="onCreate" />
  </div>
</template>
