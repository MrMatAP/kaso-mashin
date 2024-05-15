<script setup lang="ts">
import {computed, reactive, ref} from 'vue'
import {DialogKind} from '@/constants'
import {Identity, IdentityKind} from '@/store/identities'

const props = defineProps<{
  kind: DialogKind,
  input?: Identity
}>()
const emits = defineEmits<{
  (e: 'accept', output: Identity): void,
  (e: 'cancel'): void
}>()

const isOpen = ref(false)
const title = computed( () => {
  switch (props.kind) {
    case DialogKind.create: return 'Create Identity'
    case DialogKind.modify: return 'Modify Identity'
    case DialogKind.remove: return 'Remove Identity'
    default: return 'OK'
  }
})
const acceptLabel = computed( () => {
  switch(props.kind) {
    case DialogKind.create: return 'Save'
    case DialogKind.modify: return 'Modify'
    case DialogKind.remove: return 'Remove'
    default: return 'OK'
  }
})
const legalIdentityKinds = computed(() => [
  {
    value: IdentityKind.pubkey,
    title: Identity.displayKind(IdentityKind.pubkey)
  },
  {
    value: IdentityKind.password,
    title: Identity.displayKind(IdentityKind.password)
  }
])

let currentItem = reactive(props.input || Identity.defaultIdentity())
let form = ref()
const rules = {
  required: (value: any) => !!value || 'Required',
  min_2: (value: any) => {
    if (currentItem.kind !== IdentityKind.password) { return true }
    return !!value && value.length >= 2 || 'Minimum 2 characters'
  },
  has_key: () => {
    if(currentItem.kind !== IdentityKind.pubkey) { return true }
    return currentItem.pubkey !== undefined && currentItem.pubkey.length > 0 || 'You must upload an SSH public key'
  }
}

async function onAccept() {
  const formValidation = await form.value.validate();
  if(props.kind === DialogKind.remove || formValidation.valid) {
    emits('accept', currentItem)
    isOpen.value = false
  }
}

function onCancel() {
  currentItem = Identity.defaultIdentity()
  isOpen.value = false
  emits('cancel')
}
</script>

<template>
  <v-dialog v-model="isOpen" activator='parent' :persistent="true">
    <v-card>
      <v-card-title><span class="text-h5">{{ title }}</span></v-card-title>
      <v-card-text>
        <v-form ref="form">
          <v-container>
          <v-row>
            <v-col cols="6" sm="6" md="6">
              <v-text-field v-model="currentItem.name"
                            variant="underlined"
                            :clearable="true"
                            :rules="[rules.min_2]"
                            :disabled="kind === DialogKind.remove"
                            label="Login"/>
            </v-col>
            <v-col cols="6" sm="6" md="6">
                <v-select
                  v-model="currentItem.kind"
                  :items="legalIdentityKinds"
                  item-title="title"
                  item-value="value"
                  :disabled="kind !== DialogKind.create"
                  variant="underlined"
                  label="Kind"
                  required></v-select>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="4" sm="4" md="4">
              <v-text-field v-model="currentItem.gecos"
                            variant="underlined"
                            :clearable="true"
                            :disabled="kind === DialogKind.remove"
                            label="GECOS"/>
            </v-col>
            <v-col cols="4" sm="4" md="4">
              <v-text-field v-model="currentItem.shell"
                            variant="underlined"
                            :clearable="true"
                            :disabled="kind === DialogKind.remove"
                            label="Shell"/>
            </v-col>
            <v-col cols="4" sm="4" md="4">
              <v-text-field v-model="currentItem.homedir"
                            variant="underlined"
                            :clearable="true"
                            :disabled="kind === DialogKind.remove"
                            label="Home Directory"/>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6" sm="6" md="6">
              <v-text-field
                v-model="currentItem.passwd"
                type="password"
                variant="underlined"
                :rules="[rules.min_2]"
                :clearable="true"
                :disabled="currentItem.kind === IdentityKind.pubkey || kind === DialogKind.remove"
                label="Password"/>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" sm="12" md="12">
              <v-textarea
                v-model="currentItem.pubkey"
                :clearable="true"
                :rules="[rules.has_key]"
                :disabled="currentItem.kind === IdentityKind.password || kind === DialogKind.remove"
                label="SSH Public Key"></v-textarea>
            </v-col>
          </v-row>
        </v-container>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="blue-darken-1" :rounded="true" @click="onCancel">Cancel</v-btn>
        <v-btn type="submit" :rounded="true" @click="onAccept">{{ acceptLabel }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>

</style>
