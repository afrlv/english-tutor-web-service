<script setup lang="ts">
import Avatar from "primevue/avatar";
import Button from "primevue/button";
import Card from "primevue/card";
import Checkbox from "primevue/checkbox";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Tag from "primevue/tag";
import Textarea from "primevue/textarea";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref } from "vue";

import {
  addMyComment,
  fetchCabinet,
  markHomework,
  myCardSets,
  myComments,
  uploadAvatar,
} from "../../api";
import type { Cabinet, CardSetSummary, Comment } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import AttachmentList from "../../components/AttachmentList.vue";
import { useAuthStore } from "../../stores/auth";
import { formatDateTime } from "../../utils/format";

const toast = useToast();
const auth = useAuthStore();

const cabinet = ref<Cabinet | null>(null);
const comments = ref<Comment[]>([]);
const cardSets = ref<CardSetSummary[]>([]);
const newComment = ref("");
const fileInput = ref<HTMLInputElement | null>(null);

const upcoming = computed(
  () =>
    cabinet.value?.lessons
      .filter((l) => l.status === "planned")
      .sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at)) ?? [],
);
const past = computed(
  () => cabinet.value?.lessons.filter((l) => l.status === "conducted") ?? [],
);

async function load() {
  [cabinet.value, comments.value, cardSets.value] = await Promise.all([
    fetchCabinet(),
    myComments(),
    myCardSets(),
  ]);
}

onMounted(load);

async function onAvatarChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  try {
    const user = await uploadAvatar(file);
    if (cabinet.value) cabinet.value.user = user;
    if (auth.user) auth.user.avatar_path = user.avatar_path;
    toast.add({ severity: "success", summary: "Аватарка обновлена", life: 3000 });
  } catch (e: unknown) {
    const detail =
      (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
      "Не удалось загрузить файл";
    toast.add({ severity: "error", summary: "Ошибка", detail, life: 4000 });
  }
}

const answerDrafts = ref<Record<number, string>>({});

async function onToggleHomework(id: number, is_done: boolean) {
  await markHomework(id, { is_done });
  await load();
}

async function onSaveAnswer(id: number) {
  const answer = answerDrafts.value[id]?.trim();
  if (!answer) return;
  await markHomework(id, { student_answer: answer });
  delete answerDrafts.value[id];
  await load();
  toast.add({ severity: "success", summary: "Ответ сохранён", life: 3000 });
}

async function onAddComment() {
  if (!newComment.value.trim()) return;
  await addMyComment(newComment.value.trim());
  newComment.value = "";
  comments.value = await myComments();
}
</script>

<template>
  <AppLayout>
    <div class="grid">
      <Card>
        <template #title>
          <div class="profile">
            <Avatar
              :image="cabinet?.user.avatar_path ? `/media/${cabinet.user.avatar_path}` : undefined"
              :label="cabinet?.user.avatar_path ? undefined : cabinet?.user.full_name?.[0]"
              size="xlarge"
              shape="circle"
            />
            <div>
              {{ cabinet?.user.full_name }}
              <div>
                <Button
                  label="Сменить аватарку"
                  icon="pi pi-camera"
                  text
                  size="small"
                  @click="fileInput?.click()"
                />
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  hidden
                  @change="onAvatarChange"
                />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Ближайшие уроки</template>
        <template #content>
          <DataTable :value="upcoming">
            <template #empty>Запланированных уроков нет</template>
            <Column header="Когда">
              <template #body="{ data }">{{ formatDateTime(data.scheduled_at) }}</template>
            </Column>
            <Column field="topic" header="Тема" />
            <Column header="Zoom">
              <template #body="{ data }">
                <a v-if="data.zoom_link" :href="data.zoom_link" target="_blank">
                  Подключиться
                </a>
              </template>
            </Column>
            <Column field="recommendation" header="Рекомендации" />
          </DataTable>
        </template>
      </Card>

      <Card>
        <template #title>Домашние задания</template>
        <template #content>
          <template v-for="lesson in cabinet?.lessons ?? []" :key="lesson.id">
            <div v-if="lesson.homeworks.length" class="hw-lesson">
              <strong>{{ formatDateTime(lesson.scheduled_at) }}</strong>
              <span v-if="lesson.topic"> — {{ lesson.topic }}</span>
              <div v-for="hw in lesson.homeworks" :key="hw.id" class="hw-item">
                <div class="hw-row">
                  <Checkbox
                    :model-value="hw.is_done"
                    binary
                    @update:model-value="(v: boolean) => onToggleHomework(hw.id, v)"
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
            </div>
          </template>
          <p v-if="!cabinet?.lessons.some((l) => l.homeworks.length)">Заданий пока нет</p>
        </template>
      </Card>

      <Card v-if="cardSets.length">
        <template #title>Карточки для запоминания</template>
        <template #content>
          <div v-for="s in cardSets" :key="s.id" class="set-row">
            <span class="set-title">{{ s.title }}</span>
            <span class="set-progress">{{ s.learned }} / {{ s.total }} выучено</span>
            <Button
              label="Учить"
              icon="pi pi-play"
              size="small"
              @click="$router.push(`/study/${s.id}`)"
            />
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Прошедшие уроки</template>
        <template #content>
          <DataTable :value="past">
            <template #empty>Проведённых уроков пока нет</template>
            <Column header="Когда">
              <template #body="{ data }">{{ formatDateTime(data.scheduled_at) }}</template>
            </Column>
            <Column field="topic" header="Что проходили" />
            <Column field="recommendation" header="Рекомендации" />
            <Column header="">
              <template #body><Tag value="Проведён" severity="success" /></template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <Card>
        <template #title>Мои комментарии</template>
        <template #content>
          <div v-for="c in comments" :key="c.id" class="comment">
            <strong>{{ c.author_name }}</strong>
            <span class="comment-date">{{ formatDateTime(c.created_at) }}</span>
            <p>{{ c.body }}</p>
          </div>
          <div class="comment-form">
            <Textarea v-model="newComment" rows="2" placeholder="Написать комментарий" fluid />
            <Button label="Отправить" @click="onAddComment" />
          </div>
        </template>
      </Card>
    </div>
  </AppLayout>
</template>

<style scoped>
.grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.profile {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.hw-lesson {
  margin-bottom: 0.75rem;
}
.set-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.4rem 0;
}
.set-title {
  font-weight: 600;
  min-width: 10rem;
}
.set-progress {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
.hw-item {
  margin: 0.4rem 0 0.75rem;
}
.answer {
  margin: 0.3rem 0 0;
  font-size: 0.9rem;
  font-style: italic;
  color: var(--p-text-muted-color);
}
.answer-form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.4rem;
  margin-top: 0.4rem;
  max-width: 28rem;
}
.hw-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}
.done {
  text-decoration: line-through;
  color: var(--p-text-muted-color);
}
.comment {
  border-bottom: 1px solid var(--p-surface-200);
  padding: 0.5rem 0;
}
.comment p {
  margin: 0.25rem 0 0;
}
.comment-date {
  margin-left: 0.5rem;
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
}
.comment-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}
</style>
