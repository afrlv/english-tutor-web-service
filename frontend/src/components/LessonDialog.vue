<script setup lang="ts">
import Button from "primevue/button";
import DatePicker from "primevue/datepicker";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Textarea from "primevue/textarea";
import { computed, ref, watch } from "vue";

import type { Lesson, Student } from "../api/types";

const props = defineProps<{
  lesson?: Lesson | null;
  /** Если передан список — диалог показывает выбор ученика (создание из календаря) */
  students?: Student[];
  /** Предзаполнить дату/время (клик по слоту календаря) */
  initialDate?: Date | null;
}>();
const visible = defineModel<boolean>("visible", { required: true });
const emit = defineEmits<{
  save: [
    data: {
      scheduled_at: string;
      topic?: string;
      zoom_link?: string;
      recommendation?: string;
    },
    studentId: number | null,
  ];
}>();

const scheduledAt = ref<Date | null>(null);
const topic = ref("");
const zoomLink = ref("");
const recommendation = ref("");
const studentId = ref<number | null>(null);

const needStudent = computed(() => props.students !== undefined && !props.lesson);
const studentOptions = computed(
  () => props.students?.map((s) => ({ label: s.user.full_name, value: s.id })) ?? [],
);
const canSave = computed(
  () => scheduledAt.value !== null && (!needStudent.value || studentId.value !== null),
);

watch(visible, (open) => {
  if (!open) return;
  scheduledAt.value = props.lesson
    ? new Date(props.lesson.scheduled_at)
    : (props.initialDate ?? null);
  topic.value = props.lesson?.topic ?? "";
  zoomLink.value = props.lesson?.zoom_link ?? "";
  recommendation.value = props.lesson?.recommendation ?? "";
  studentId.value = null;
});

function submit() {
  if (!canSave.value) return;
  emit(
    "save",
    {
      scheduled_at: scheduledAt.value!.toISOString(),
      topic: topic.value || undefined,
      zoom_link: zoomLink.value || undefined,
      recommendation: recommendation.value || undefined,
    },
    studentId.value,
  );
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    :header="lesson ? 'Изменить урок' : 'Новый урок'"
    modal
  >
    <form class="form" @submit.prevent="submit">
      <label v-if="needStudent">
        Ученик
        <Select
          v-model="studentId"
          :options="studentOptions"
          option-label="label"
          option-value="value"
          placeholder="Выберите ученика"
          fluid
        />
      </label>
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
      <Button type="submit" label="Сохранить" :disabled="!canSave" />
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
