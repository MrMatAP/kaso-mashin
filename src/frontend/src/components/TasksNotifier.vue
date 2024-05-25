<script setup lang="ts">
import { onMounted, Ref, ref } from "vue";
import { useInterval, useQuasar } from "quasar";
import { TaskGetSchema, TaskState, useTaskStore } from "@/store/tasks";
import { EntityNotFoundException } from "@/base_types";

const $q = useQuasar();
const { registerInterval } = useInterval();
const taskStore = useTaskStore();
const currentTab: Ref<string> = ref('tasks')

const pendingTasks: Ref<TaskGetSchema[]> = ref<TaskGetSchema[]>([]);

async function updatePendingTasks() {
  try {
    for(const task of taskStore.pendingTasks) {
      let pendingTask = await taskStore.get(task.uid)
      if(pendingTask.state === TaskState.FAILED) {
        $q.notify({ message: pendingTask.msg, type: "error", icon: 'error'});
      } else if(pendingTask.state === TaskState.DONE) {
        $q.notify({ message: pendingTask.msg });
      } else {
        pendingTasks.value.push(pendingTask)
      }
    }
  } catch(e) {
    $q.notify({ message: (e as EntityNotFoundException).msg, icon: 'error' })
  }
}

onMounted( async () => {
  await taskStore.list()
  registerInterval(async () => await updatePendingTasks(), 3000)
})
</script>

<template>
  <q-btn round dense flat color="grey-8" icon="notifications">
    <q-badge
      color="red"
      text-color="white"
      floating
      v-show="taskStore.pendingNumber > 0"
    >
      {{ taskStore.pendingNumber }}
    </q-badge>
    <q-tooltip>Tasks</q-tooltip>
    <q-menu style="max-width: 500px">
      <q-tabs v-model="currentTab">
        <q-tab name="tasks" label="Tasks">
          <q-list dense>
            <q-item v-close-popup v-for="task in taskStore.tasks">
              <q-item-section avatar>
                <q-avatar color="primary" text-color="white" icon="bluetooth"/>
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ task.name }}</q-item-label>
                <q-item-label caption lines="2">{{ task.msg }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-item-label caption>{{ task.state }}</q-item-label>
                <q-circular-progress show-value
                                     v-show="task.state === TaskState.RUNNING"
                                     :value="task.percent_complete"
                                     class="text-light-blue q-ma-md"
                                     color="light-blue"
                                     size="xs"/>
              </q-item-section>
            </q-item>
          </q-list>
        </q-tab>
        <q-tab name="error" label="Errors">
          <q-list>
            <q-item v-close-popup>
              <q-item-section>
                <q-item-label>There are no errors</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-tab>
      </q-tabs>
    </q-menu>
  </q-btn>
</template>

<style scoped>

</style>
