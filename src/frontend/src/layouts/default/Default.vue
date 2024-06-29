<script lang="ts" setup>
import { ref } from "vue";
import { useConfigStore } from "@/store/config";
import { useTaskStore } from "@/store/tasks";
import { useErrorStore } from "@/store/errors";
import TaskCards from "@/components/TaskCards.vue";
import ErrorCards from "@/components/ErrorCards.vue";

const configStore = useConfigStore();
const taskStore = useTaskStore();
const errorStore = useErrorStore();
const drawerOpen = ref(false);

async function onToggleDrawer() {
  drawerOpen.value = !drawerOpen.value;
}
</script>

<template>
  <q-layout>
    <q-header elevated height-hint="58" class="bg-white text-grey-8 q-py-xs">
      <q-toolbar>
        <q-btn flat dense round @click="onToggleDrawer" aria-label="Menu" icon="menu" />
        <q-btn flat no-caps no-wrap v-if="$q.screen.gt.xs">
          <q-toolbar-title shrink class="text-weight-bold">Kaso :: Mashin</q-toolbar-title>
        </q-btn>
        <q-space />
      </q-toolbar>
    </q-header>

    <q-drawer :v-model="drawerOpen" show-if-above bordered class="bg-grey-2" :width="240">
      <q-scroll-area class="fit">
        <q-list padding>
          <q-item v-ripple clickable :to="{ name: 'Instances' }">
            <q-item-section avatar>
              <q-icon name="developer_board" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Instances</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-ripple clickable :to="{ name: 'Identities' }">
            <q-item-section avatar>
              <q-icon name="fingerprint" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Identities</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-ripple clickable :to="{ name: 'Networks' }">
            <q-item-section avatar>
              <q-icon name="settings_ethernet" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Networks</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-ripple clickable :to="{ name: 'Images' }">
            <q-item-section avatar>
              <q-icon name="work_outline" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Images</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-ripple clickable :to="{ name: 'Bootstraps' }">
            <q-item-section avatar>
              <q-icon name="start" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Bootstraps</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
        <q-space />
        <div class="absolute-bottom" style="max-height: 50%">
          <q-list>
            <q-separator />
            <q-expansion-item expand-separator group="info" default-opened style="overflow-y: auto">
              <template v-slot:header>
                <q-item-section avatar>
                  <q-avatar icon="task_alt" />
                </q-item-section>
                <q-item-section>Tasks</q-item-section>
                <q-badge
                  color="red"
                  text-color="white"
                  rounded
                  v-show="taskStore.runningTasks.length > 0"
                  >{{ taskStore.runningTasks.length }}
                </q-badge>
              </template>
              <TaskCards />
            </q-expansion-item>
            <q-expansion-item expand-separator group="info" style="overflow-y: auto">
              <template v-slot:header>
                <q-item-section avatar>
                  <q-avatar icon="error" />
                </q-item-section>
                <q-item-section>Errors</q-item-section>
                <q-badge
                  color="red"
                  text-color="white"
                  rounded
                  v-show="errorStore.errors.length > 0"
                  >{{ errorStore.errors.length }}
                </q-badge>
              </template>
              <ErrorCards />
            </q-expansion-item>
            <q-item dense>
              <q-item-label caption>{{ configStore.config.version }}</q-item-label>
            </q-item>
          </q-list>
        </div>
      </q-scroll-area>
    </q-drawer>

    <q-page-container>
      <div id="content">
        <router-view></router-view>
      </div>
    </q-page-container>
  </q-layout>
</template>

<style scoped>
#content {
  padding-left: 20px;
  padding-right: 20px;
}
</style>
