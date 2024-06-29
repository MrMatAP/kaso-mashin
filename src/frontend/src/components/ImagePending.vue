<script setup lang="ts">
import { ref, Ref, onMounted } from "vue";
import { useQuasar } from "quasar";
import { ImageCreateSchema } from "@/store/images";
import { TaskGetSchema, TaskState, useTaskStore } from "@/store/tasks";
import { useImageStore } from "@/store/images";

const props = defineProps<{
  taskUid: string;
  image: ImageCreateSchema;
}>();

const quasar = useQuasar();
const taskStore = useTaskStore();
const imageStore = useImageStore();
const task: Ref<TaskGetSchema> = ref(new TaskGetSchema());

onMounted(async () => {
  taskStore.$subscribe(async (mutation, state) => {
    task.value = state.tasks.get(props.taskUid) as TaskGetSchema;
    if (task.value.state == TaskState.FAILED) {
      imageStore.pendingImages.delete(props.taskUid);
      quasar.notify({ message: task.value.msg, type: "error", icon: "error" });
    } else if (task.value.state === TaskState.DONE) {
      imageStore.pendingImages.delete(props.taskUid);
      // Don't use an action here, it may cause an infinite loop
      await imageStore.get(task.value.outcome as string);
      quasar.notify({ message: task.value.msg });
    }
  });
});
</script>

<template>
  <q-card class="km-entity-card">
    <q-item>
      <q-item-section side>
        <q-avatar icon="work_outline" size="lg" color="primary" text-color="white" />
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

    <q-inner-loading :showing="task.state === TaskState.RUNNING" :label="task.msg">
      <q-circular-progress
        show-value
        :value="task.percent_complete"
        size="xl"
        color="primary"
        class="q-ma-md"
        >{{ task.percent_complete }}%
      </q-circular-progress>
    </q-inner-loading>
  </q-card>
</template>
