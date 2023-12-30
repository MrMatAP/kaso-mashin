<script setup lang="ts">
import {computed, ref, reactive} from 'vue'
import {Image, PredefinedImage} from '@/store/images'
import {DialogKind} from "@/constants";

const props = defineProps<{
  kind: DialogKind,
  input?: Image,
  predefined: PredefinedImage[]
}>()
const emits = defineEmits<{
  (e: 'accept', output: Image): void
  (e: 'cancel'): void
}>()

const isOpen = ref(false)
const title = computed( () => {
  switch(props.kind) {
    case DialogKind.create: return 'Create Image'
    case DialogKind.modify: return 'Modify Image'
    case DialogKind.remove: return 'Remove Image'
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

let currentItem = reactive(props.input || Image.defaultImage())
let form = ref()
const rules = {
  required: (value: any) => !!value || 'Required',
  min_2: (value: any) => !!value && value.length >= 2 || 'Minimum 2 characters'
}

async function onAccept() {
  const formValidation = await form.value.validate()
  if(props.kind === DialogKind.remove || formValidation.valid) {
    emits('accept', currentItem)
    isOpen.value = false
  }
}

async function onCancel() {
  currentItem = Image.defaultImage()
  isOpen.value = false
  emits('cancel')
}
</script>

<template>
  <v-dialog v-model="isOpen" activator="parent" :persistent="true">
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
                              :disabled="kind !== DialogKind.create"
                              label="Name"/>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6" sm="6" md="6">
                <v-select v-model="currentItem.url"
                          :items="predefined"
                          item-title="name"
                          item-value="url"
                          variant="underlined"
                          :disabled="kind !== DialogKind.create"
                          label="Predefined URL"/>
              </v-col>
              <v-col cols="6" sm="6" md="6">
                <v-text-field v-model="currentItem.url"
                              variant="underlined"
                              :clearable="true"
                              :disabled="kind !== DialogKind.create"
                              label="URL"/>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="4" sm="4" md="4">
                <div class="text-caption">Minimum CPUs</div>
                <v-slider v-model="currentItem.min_cpu"
                          step="1"
                          :max="16"
                          show-ticks="always"
                          thumb-label="always"
                          density="compact"/>
              </v-col>
              <v-col cols="4" sm="4" md="4">
                <div class="text-caption">Minimum RAM (G)</div>
                <v-slider v-model="currentItem.min_ram"
                          step="1"
                          :max="16"
                          show-ticks="always"
                          thumb-label="always"
                          density="compact"/>
              </v-col>
              <v-col cols="4" sm="4" md="4">
                <div class="text-caption">Minimum Space (G)</div>
                <v-slider v-model="currentItem.min_space"
                          :step="1"
                          :max="16"
                          show-ticks="always"
                          thumb-label="always"
                          density="compact"/>
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
