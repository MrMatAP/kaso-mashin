<script setup lang="ts">
import { onMounted, Ref, ref } from "vue";
import { useInterval, useQuasar } from "quasar";
import { TaskGetSchema, TaskState, useTaskStore } from "@/store/tasks";
import { EntityNotFoundExceptionSchema } from "@/base_types";

const $q = useQuasar();
const { registerInterval } = useInterval()
const taskStore = useTaskStore();

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
    $q.notify({ message: (e as EntityNotFoundExceptionSchema).msg, icon: 'error' })
  }
}

onMounted( async () => {
  await taskStore.list()
  registerInterval(async () => updatePendingTasks, 3000)
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
    <q-menu style="max-width: 300px">
      <q-list style="min-width: 100px">
        <q-item v-close-popup v-show="pendingTasks.length === 0">
          <q-item-section>
            <q-item-label>There are no active tasks</q-item-label>
          </q-item-section>
        </q-item>
        <q-item v-close-popup v-for="task in pendingTasks">
          <q-item-section>
            <q-item-label>{{ task.name }}</q-item-label>
            <q-item-label caption>{{ task.msg }}</q-item-label>
          </q-item-section>
          <q-item-section side top>
            <q-item-label caption>{{ task.state }}</q-item-label>
            <q-circular-progress show-value
                                 :value="task.percent_complete"
                                 class="text-light-blue q-ma-md"
                                 color="light-blue"
                                 size="xs"/>
            <q-item-label>{{ task.percent_complete }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>
</template>

<style scoped>

</style>
