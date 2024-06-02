<script setup lang="ts">
import { TaskGetSchema, TaskRelation, TaskState, useTaskStore } from "@/store/tasks";

const taskStore = useTaskStore();

function computeTaskIcon(task: TaskGetSchema): string {
  switch (task.relation) {
    case TaskRelation.BOOTSTRAPS:
      return "start";
    case TaskRelation.DISKS:
      return "save";
    case TaskRelation.IDENTITIES:
      return "fingerprint";
    case TaskRelation.IMAGES:
      return "work_outline";
    case TaskRelation.INSTANCES:
      return "developer_board";
    case TaskRelation.NETWORKS:
      return "settings_ethernet";
    case TaskRelation.GENERAL:
      return "task_alt";
  }
}

function computeTaskState(task: TaskGetSchema): string {
  switch (task.state) {
    case TaskState.RUNNING:
      return "run_circle";
    case TaskState.DONE:
      return "check_circle";
    case TaskState.FAILED:
      return "remove_circle_outline";
  }
}
</script>

<template>
  <q-card flat bordered v-for="task in taskStore.allTasks">
    <q-item>
      <q-item-section avatar>
        <q-avatar :icon="computeTaskIcon(task)" />
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ task.name }}</q-item-label>
        <q-item-label caption>{{ task.msg }}</q-item-label>
      </q-item-section>
      <q-item-section side>
        <q-item-label v-show="task.state !== TaskState.RUNNING">
          <q-icon :name="computeTaskState(task)" />
        </q-item-label>
        <q-circular-progress
          show-value
          v-show="task.state === TaskState.RUNNING"
          :value="task.percent_complete"
          class="text-light-blue q-ma-md"
          color="primary"
          size="md"
        />
      </q-item-section>
    </q-item>
  </q-card>
</template>

<style scoped></style>
