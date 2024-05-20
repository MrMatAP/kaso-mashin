<script setup lang="ts">
import { ref, Ref, onMounted } from 'vue';
import { useInterval, useQuasar } from 'quasar';
import { ImageCreateSchema, useImageStore } from "@/store/images";
import { TaskGetSchema, TaskState, useTaskStore } from "@/store/tasks";

const props = defineProps<{
  taskUid: string;
  image: ImageCreateSchema;
}>();
defineEmits<{
  (e: "onSelected", uid: string): void;
}>();

const quasar = useQuasar();
const { registerInterval } = useInterval();
const taskStore = useTaskStore();
const imageStore = useImageStore();
const task: Ref<TaskGetSchema> = ref(new TaskGetSchema());

onMounted(async () => {
  task.value = await taskStore.get(props.taskUid);
  registerInterval(async () => {
    task.value = await taskStore.get(props.taskUid);
    if(task.value.state === TaskState.FAILED) {
      imageStore.pendingImages.delete(props.taskUid);
      quasar.notify({ message: task.value.msg, type: "error", icon: 'error' })
    }
    if(task.value.state === TaskState.DONE) {
      imageStore.pendingImages.delete(props.taskUid);
      quasar.notify({ message: task.value.msg })
    }
  }, 3000)
})

</script>

<template>
  <q-card class="km-entity-card">
    <q-item>
      <q-item-section side>
        <q-avatar icon="work_outline" size="lg" color="primary" text-color="white"/>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ image.name }}</q-item-label>
        <q-item-label caption></q-item-label>
      </q-item-section>
    </q-item>
    <q-separator />
    <q-markup-table>
      <tbody>
        <tr>
          <td class="text-left">Minimum vCPU</td>
          <td class="text-right">{{ image.min_vcpu }}</td>
        </tr>
        <tr>
          <td class="text-left">Minimum RAM</td>
          <td class="text-right">{{ image.min_ram.value }}</td>
        </tr>
        <tr>
          <td class="text-left">Minimum Disk Space</td>
          <td class="text-right">{{ image.min_disk.value }}</td>
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
