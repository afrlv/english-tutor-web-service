<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Checkbox from "primevue/checkbox";
import Tag from "primevue/tag";
import Textarea from "primevue/textarea";
import { useToast } from "primevue/usetoast";
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { markHomework, myLesson, myLessonCardSets } from "../../api";
import type { CardSetSummary, Lesson } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import AttachmentList from "../../components/AttachmentList.vue";
import { formatDateTime } from "../../utils/format";
import { statusLabel, statusSeverity } from "../../utils/lessons";

const route = useRoute();
const router = useRouter();
const toast = useToast();
const lessonId = Number(route.params.id);

const lesson = ref<Lesson | null>(null);
const cardSets = ref<CardSetSummary[]>([]);
const answerDrafts = ref<Record<number, string>>({});

async function load() {
  try {
    lesson.value = await myLesson(lessonId);
    cardSets.value = await myLessonCardSets(lessonId);
  } catch {
    router.push("/cabinet");
  }
}
load();

async function onToggle(hwId: number, is_done: boolean) {
  await markHomework(hwId, { is_done });
  await load();
}

async function onSaveAnswer(hwId: number) {
  const answer = answerDrafts.value[hwId]?.trim();
  if (!answer) return;
  await markHomework(hwId, { student_answer: answer });
  delete answerDrafts.value[hwId];
  await load();
  toast.add({ severity: "success", summary: "Ответ сохранён", life: 3000 });
}
</script>

<template>
  <AppLayout>
    <template v-if="lesson">
      <Card class="mb">
        <template #title>
          <div class="head">
            <Button icon="pi pi-arrow-left" text rounded @click="router.push('/cabinet')" />
            <div class="head-main">
              <span>{{ lesson.topic || "Урок" }}</span>
              <span class="when">{{ formatDateTime(lesson.scheduled_at) }}</span>
            </div>
            <Tag :value="statusLabel(lesson.status)" :severity="statusSeverity(lesson.status)" />
          </div>
        </template>
        <template #content>
          <a v-if="lesson.zoom_link" :href="lesson.zoom_link" target="_blank">
            <Button label="Подключиться к Zoom" icon="pi pi-video" />
          </a>
          <p v-if="lesson.recommendation" class="pre rec">
            <strong>Рекомендации учителя:</strong><br />{{ lesson.recommendation }}
          </p>
        </template>
      </Card>

      <Card v-if="lesson.attachments.length" class="mb">
        <template #title>Материалы урока</template>
        <template #content>
          <AttachmentList :attachments="lesson.attachments" />
        </template>
      </Card>

      <Card v-if="cardSets.length" class="mb">
        <template #title>Карточки для запоминания</template>
        <template #content>
          <div v-for="s in cardSets" :key="s.id" class="set-row">
            <span class="set-title">{{ s.title }}</span>
            <span class="set-progress">{{ s.learned }} / {{ s.total }} выучено</span>
            <Button
              label="Учить"
              icon="pi pi-play"
              size="small"
              @click="router.push(`/study/${s.id}`)"
            />
          </div>
        </template>
      </Card>

      <Card class="mb">
        <template #title>Домашнее задание</template>
        <template #content>
          <div v-for="hw in lesson.homeworks" :key="hw.id" class="hw">
            <div class="hw-head">
              <Checkbox
                :model-value="hw.is_done"
                binary
                @update:model-value="(v: boolean) => onToggle(hw.id, v)"
              />
              <span :class="{ done: hw.is_done }">{{ hw.description }}</span>
              <Tag
                v-if="hw.grade"
                :value="`Оценка: ${hw.grade}`"
                :severity="hw.grade >= 4 ? 'success' : hw.grade === 3 ? 'warn' : 'danger'"
              />
              <Tag v-else-if="hw.checked_at" value="Проверено" severity="success" />
            </div>
            <AttachmentList :attachments="hw.attachments" />
            <p v-if="hw.student_answer && answerDrafts[hw.id] === undefined" class="answer">
              Мой ответ: {{ hw.student_answer }}
              <Button
                label="изменить"
                text
                size="small"
                @click="answerDrafts[hw.id] = hw.student_answer ?? ''"
              />
            </p>
            <div v-else class="answer-form">
              <Textarea
                :model-value="answerDrafts[hw.id] ?? ''"
                rows="2"
                placeholder="Написать ответ"
                fluid
                @update:model-value="(v: string) => (answerDrafts[hw.id] = v)"
              />
              <Button
                label="Сохранить ответ"
                size="small"
                :disabled="!answerDrafts[hw.id]?.trim()"
                @click="onSaveAnswer(hw.id)"
              />
            </div>
          </div>
          <p v-if="!lesson.homeworks.length" class="muted">К этому уроку заданий нет</p>
        </template>
      </Card>
    </template>
  </AppLayout>
</template>

<style scoped>
.mb {
  margin-bottom: 1rem;
}
.head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.head-main {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex: 1;
}
.when {
  font-size: 0.9rem;
  font-weight: 400;
  color: var(--p-text-muted-color);
}
.rec {
  margin-top: 1rem;
}
.pre {
  white-space: pre-wrap;
}
.hw {
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--p-surface-200);
}
.hw-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.hw-head span {
  flex: 1;
}
.done {
  text-decoration: line-through;
  color: var(--p-text-muted-color);
}
.answer {
  margin: 0.3rem 0 0;
  font-style: italic;
  color: var(--p-text-muted-color);
}
.answer-form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.4rem;
  margin-top: 0.4rem;
  max-width: 30rem;
}
.muted {
  color: var(--p-text-muted-color);
}
.set-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.4rem 0;
}
.set-title {
  font-weight: 600;
  flex: 1;
}
.set-progress {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
</style>
