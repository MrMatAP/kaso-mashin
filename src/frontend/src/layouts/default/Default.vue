<script lang="ts" setup>
import { ref } from "vue";
import { useConfigStore } from "@/store/config";
import TasksNotifier from "@/components/TasksNotifier.vue";

const configStore = useConfigStore();
const drawerOpen = ref(false);

async function onToggleDrawer() {
  drawerOpen.value = !drawerOpen.value;
}
</script>

<template>
  <q-layout>
    <q-header elevated height-hint="58" class="bg-white text-grey-8 q-py-xs">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          @click="onToggleDrawer"
          aria-label="Menu"
          icon="menu"
        />
        <q-btn flat no-caps no-wrap v-if="$q.screen.gt.xs">
          <q-toolbar-title shrink class="text-weight-bold"
            >Kaso :: Mashin - {{ configStore.config.version }}</q-toolbar-title
          >
        </q-btn>
        <q-space />
        <div class="q-gutter-sm row items-center no-wrap">
          <TasksNotifier/>
          <q-btn round flat>
            <q-avatar size="26px">
              <img src="https://cdn.quasar.dev/img/boy-avatar.png" />
            </q-avatar>
            <q-tooltip>Account</q-tooltip>
          </q-btn>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer
      :v-model="drawerOpen"
      show-if-above
      bordered
      class="bg-grey-2"
      :width="240"
    >
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
          <q-separator class="q-my-md" />
        </q-list>
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
