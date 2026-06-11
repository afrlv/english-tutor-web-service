<script setup lang="ts">
import Button from "primevue/button";
import DatePicker from "primevue/datepicker";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import { ref, watch } from "vue";

import type { Lesson } from "../api/types";

const props = defineProps<{ lesson?: Lesson | null }>();
const visible = defineModel<boolean>("visible", { required: true });
const emit = defineEmits<{
  save: [
    data: { scheduled_at: string; topic?: string; zoom_link?: string; recommendation?: string },
  ];
}>();

const scheduledAt = ref<Date | null>(null);
const topic = ref("");
const zoomLink = ref("");
const recommendation = ref("");

watch(visible, (open) => {
  if (!open) return;
  scheduledAt.value = props.lesson ? new Date(props.lesson.scheduled_at) : null;
  topic.value = props.lesson?.topic ?? "";
  zoomLink.value = props.lesson?.zoom_link ?? "";
  recommendation.value = props.lesson?.recommendation ?? "";
});

function submit() {
  if (!scheduledAt.value) return;
  emit("save", {
    scheduled_at: scheduledAt.value.toISOString(),
    topic: topic.value || undefined,
    zoom_link: zoomLink.value || undefined,
    recommendation: recommendation.value || undefined,
  });
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    :header="lesson ? 'Изменить урок' : 'Новый урок'"
    modal
  >
    <form class="form" @submit.prevent="submit">
      <label>
        Дата и время
        <DatePicker
          v-model="scheduledAt"
          show-time
          hour-format="24"
          date-format="dd.mm.yy"
          fluid
        />
      </label>
      <label>
        Тема урока
        <InputText v-model="topic" fluid />
      </label>
      <label>
        Ссылка на Zoom
        <InputText v-model="zoomLink" fluid />
      </label>
      <label>
        Рекомендации и советы
        <Textarea v-model="recommendation" rows="3" fluid />
      </label>
      <Button type="submit" label="Сохранить" :disabled="!scheduledAt" />
    </form>
  </Dialog>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 22rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}
</style>
