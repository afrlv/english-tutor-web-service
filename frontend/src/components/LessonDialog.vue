<script setup lang="ts">
import Button from "primevue/button";
import Checkbox from "primevue/checkbox";
import DatePicker from "primevue/datepicker";
import Dialog from "primevue/dialog";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import SelectButton from "primevue/selectbutton";
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
      duration_minutes?: number;
      price?: string | null;
      topic?: string;
      zoom_link?: string;
      recommendation?: string;
    },
    studentId: number | null,
  ];
}>();

const scheduledAt = ref<Date | null>(null);
const duration = ref(60);
const isFree = ref(false);
const customPrice = ref<number | null>(null);
const topic = ref("");
const zoomLink = ref("");
const recommendation = ref("");
const studentId = ref<number | null>(null);

const durationOptions = [
  { label: "45 мин", value: 45 },
  { label: "60 мин", value: 60 },
  { label: "90 мин", value: 90 },
];

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
  duration.value = props.lesson?.duration_minutes ?? 60;
  const price = props.lesson?.price != null ? parseFloat(props.lesson.price) : null;
  isFree.value = price === 0;
  customPrice.value = price && price > 0 ? price : null;
  topic.value = props.lesson?.topic ?? "";
  zoomLink.value = props.lesson?.zoom_link ?? "";
  recommendation.value = props.lesson?.recommendation ?? "";
  studentId.value = null;
});

function submit() {
  if (!canSave.value) return;
  // Цена: бесплатный → "0"; своя сумма → она; иначе null (цена с карточки родителя)
  const price = isFree.value ? "0" : customPrice.value ? String(customPrice.value) : null;
  emit(
    "save",
    {
      scheduled_at: scheduledAt.value!.toISOString(),
      duration_minutes: duration.value,
      price,
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
        Длительность
        <SelectButton
          v-model="duration"
          :options="durationOptions"
          option-label="label"
          option-value="value"
          :allow-empty="false"
        />
      </label>
      <div class="price-row">
        <label class="free-toggle">
          <Checkbox v-model="isFree" binary />
          Бесплатный (пробный)
        </label>
        <label v-if="!isFree" class="price-field">
          Цена (пусто — с карточки родителя)
          <InputNumber
            v-model="customPrice"
            :min="0"
            mode="currency"
            currency="RUB"
            locale="ru-RU"
            fluid
          />
        </label>
      </div>
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
.price-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.free-toggle {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}
.price-field {
  flex: 1;
}
</style>
