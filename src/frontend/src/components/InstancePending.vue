<script setup lang="ts">
import { ref, Ref, onMounted } from 'vue';
import { useInterval, useQuasar } from 'quasar';
import { InstanceCreateSchema, useInstanceStore } from "@/store/instances";
import { TaskGetSchema, TaskState, useTaskStore } from "@/store/tasks";

const props = defineProps<{
  taskUid: string;
  instance: InstanceCreateSchema;
}>();

const quasar = useQuasar();
const { registerInterval } = useInterval();
const taskStore = useTaskStore();
const instanceStore = useInstanceStore();
const task: Ref<TaskGetSchema> = ref(new TaskGetSchema());

onMounted(async () => {
  task.value = await taskStore.get(props.taskUid);
  registerInterval(async () => {
    task.value = await taskStore.get(props.taskUid);
    if(task.value.state === TaskState.FAILED) {
      instanceStore.pendingInstances.delete(props.taskUid);
      quasar.notify({ message: task.value.msg, type: "error", icon: 'error' })
    }
    if(task.value.state === TaskState.DONE) {
      if(! task.value.outcome) {
        quasar.notify({ message: task.value.msg, type: 'error', icon: 'error' })
      } else {
        await instanceStore.get(task.value.outcome);
        quasar.notify({ message: task.value.msg })
      }
      instanceStore.pendingInstances.delete(props.taskUid);
    }
  }, 3000)
})

</script>

<template>
  <q-card class="km-entity-card">
    <q-item>
      <q-item-section side>
        <q-avatar icon="developer_board" size="lg" color="primary" text-color="white"/>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ instance.name }}</q-item-label>
        <q-item-label caption></q-item-label>
      </q-item-section>
    </q-item>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">vCPUs</td>
          <td class="text-right">{{ instance.vcpu }}</td>
        </tr>
        <tr>
          <td class="text-left">RAM</td>
          <td class="text-right">{{ instance.ram.value }} {{ instance.ram.scale }}</td>
        </tr>
      </tbody>
    </q-markup-table>

    <q-inner-loading
      :showing="task.state === TaskState.RUNNING"
      :label="task.msg">
      <q-circular-progress show-value
                           :value="task.percent_complete"
                           size="xl"
                           color="primary"
                           class="q-ma-md">{{ task.percent_complete }}%</q-circular-progress>
    </q-inner-loading>
  </q-card>
</template>
