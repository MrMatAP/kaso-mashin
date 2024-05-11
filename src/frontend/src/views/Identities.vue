<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  IdentityCreateSchema,
  IdentityGetSchema,
  IdentityModifySchema,
  useIdentitiesStore,
} from "@/store/identities";
import ExplanationNote from "@/components/ExplanationNote.vue";
//import IdentityDialog from "@/components/IdentityDialog.vue";
//import {DialogKind} from "@/constants";

const identitiesStore = useIdentitiesStore();
const loading = ref(true);

const headers = [
  {
    key: "uid",
    title: "UID",
    sortable: true,
  },
  {
    key: "name",
    title: "Name (Login)",
    sortable: true,
  },
  {
    key: "kind",
    title: "Kind",
    sortable: true,
  },
  {
    key: "gecos",
    title: "GECOS",
    sortable: true,
  },
  {
    key: "homedir",
    title: "Home Directory",
    sortable: true,
  },
  {
    key: "shell",
    title: "Shell",
    sortable: true,
  },
  {
    key: "actions",
    title: "Actions",
    sortable: false,
  },
];

function createIdentity(create: IdentityCreateSchema) {
  console.log("Would now create identity with name " + create.name);
  loading.value = true;
  identitiesStore.create(create).then(() => {
    identitiesStore.list();
    loading.value = false;
  });
}

function modifyIdentity(uid: string, modify: IdentityModifySchema) {
  console.log("Would now modify identity with name " + modify.name);
  loading.value = true;
  identitiesStore.modify(uid, modify).then(() => {
    identitiesStore.list();
    loading.value = false;
  });
}

function removeIdentity(uid: string) {
  loading.value = true;
  identitiesStore.remove(uid).then(() => {
    identitiesStore.list();
    loading.value = false;
  });
}

onMounted(() => {
  identitiesStore.list().then(() => {
    loading.value = false;
  });
});
</script>

<template>
  <v-container>
    <v-data-table
      :headers="headers"
      :items="identitiesStore.identities"
      :loading="loading"
      :sort-by="[{ key: 'uid', order: 'asc' }]"
    >
      <template v-slot:top>
        <v-toolbar>
          <v-toolbar-title>Identities</v-toolbar-title>
          <v-divider class="mx-4" :inset="true" :vertical="true"></v-divider>
          <v-spacer></v-spacer>
          <v-btn color="primary" dark class="mb-2">
            Create Identity
            <!--            <identity-dialog :kind="DialogKind.create" @accept="createIdentity"/>-->
          </v-btn>
        </v-toolbar>
      </template>
      <template v-slot:[`item.kind`]="{ value }"> value </template>
      <template v-slot:[`item.actions`]="{ item }">
        <v-btn density="compact" :rounded="true" variant="plain">
          <v-icon size="small">mdi-pencil</v-icon>
          <!--          <identity-dialog :kind="DialogKind.modify" :input="item" @accept="modifyIdentity"/>-->
        </v-btn>
        <v-btn density="compact" :rounded="true" variant="plain">
          <v-icon size="small">mdi-delete</v-icon>
          <!--          <identity-dialog :kind="DialogKind.remove" :input="item" @accept="removeIdentity"/>-->
        </v-btn>
      </template>
      <template v-slot:loading>
        <v-skeleton-loader type="table-row@10"></v-skeleton-loader>
      </template>
    </v-data-table>
    <explanation-note title="Identities">
      <template v-slot:explanation>
        <p class="text-body-2 pa-4">
          Identities enable you to log in to your virtual machines. There are
          two kinds of identities: SSH Key based and password-based.
          Password-based identities can be used to log in on the console
          directly when you need to debug or post-configured your VM. SSH
          Key-based identities are meant to be used over the network.
        </p>
        <p class="text-body-2 pa-4">
          Changes to identities only take effect when re-creating a virtual
          machine.
        </p>
      </template>
    </explanation-note>
  </v-container>
</template>

<style scoped></style>
