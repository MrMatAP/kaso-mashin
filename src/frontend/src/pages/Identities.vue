<script setup lang="ts">
import {onMounted, ref} from "vue";
import {useRouter} from 'vue-router';
import IdentityCard from "@/components/IdentityCard.vue";
import {useIdentitiesStore} from "@/store/identities";

const router = useRouter()
const store = useIdentitiesStore()
const loading = ref(true)
const confirmRemove = ref(false)

async function onModify(uid: string) {
  await router.push({ name: 'IdentitiesModify', params: { uid: uid }})
}

async function onRemove(uid: string) {

}

async function onRemoveConfirmed(uid: string) {
  await store.remove(uid)
}

async function onSelected(uid: string) {
  await router.push({ name: 'IdentityDetail', params: { uid: uid}})
}

onMounted( () => {
  store.list().then( () => { loading.value = false })
})
</script>

<template>
  <div class="row nowrap">
    <h4>Identities</h4>
  </div>
  <div class="q-pa-md row items-start q-gutter-md">
    <IdentityCard v-for="identity in store.identities"
                  :key="identity.uid"
                  :identity="identity"
                  @onSelected="onSelected"
                  @onModify="onModify"
                  @onRemove="confirmRemove = true"/>

    <q-card class="km-new-card">
      <q-card-section class="absolute-center" >
        <q-btn flat round color="primary" icon="add" :to="{name: 'IdentitiesCreate'}"/>
      </q-card-section>
    </q-card>
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary"/>
    </q-inner-loading>
  </div>
</template>
