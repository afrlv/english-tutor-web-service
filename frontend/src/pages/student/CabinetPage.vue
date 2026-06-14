<script setup lang="ts">
import Avatar from "primevue/avatar";
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Tag from "primevue/tag";
import Textarea from "primevue/textarea";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref } from "vue";

import {
  addMyComment,
  fetchCabinet,
  getProgress,
  myCardSets,
  myComments,
  uploadAvatar,
} from "../../api";
import type { Cabinet, CardSetSummary, Comment, Progress } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { useAuthStore } from "../../stores/auth";
import { formatDateTime } from "../../utils/format";

const toast = useToast();
const auth = useAuthStore();

const cabinet = ref<Cabinet | null>(null);
const comments = ref<Comment[]>([]);
const cardSets = ref<CardSetSummary[]>([]);
const progress = ref<Progress | null>(null);
const newComment = ref("");
const fileInput = ref<HTMLInputElement | null>(null);

// Предстоящие: 3 ближайших (ближайший сверху)
const upcoming = computed(
  () =>
    cabinet.value?.lessons
      .filter((l) => l.status === "planned")
      .sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at))
      .slice(0, 3) ?? [],
);
// Прошедшие: 3 последних (свежий сверху)
const past = computed(
  () =>
    cabinet.value?.lessons
      .filter((l) => l.status === "conducted")
      .sort((a, b) => b.scheduled_at.localeCompare(a.scheduled_at))
      .slice(0, 3) ?? [],
);
// Уроки с несделанными заданиями — быстрые ссылки в карточку урока
const pendingHomework = computed(
  () => cabinet.value?.lessons.filter((l) => l.homeworks.some((h) => !h.is_done)) ?? [],
);

async function load() {
  [cabinet.value, comments.value, cardSets.value, progress.value] = await Promise.all([
    fetchCabinet(),
    myComments(),
    myCardSets(),
    getProgress(),
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
              :image="cabinet?.user.avatar_path ? `/api/files/${cabinet.user.avatar_path}` : undefined"
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
          <DataTable
            :value="upcoming"
            selection-mode="single"
            @row-select="(e) => $router.push(`/my-lessons/${e.data.id}`)"
          >
            <template #empty>Запланированных уроков нет</template>
            <Column header="Когда">
              <template #body="{ data }">{{ formatDateTime(data.scheduled_at) }}</template>
            </Column>
            <Column field="topic" header="Тема" />
            <Column header="Zoom">
              <template #body="{ data }">
                <a v-if="data.zoom_link" :href="data.zoom_link" target="_blank" @click.stop>
                  Подключиться
                </a>
              </template>
            </Column>
            <Column header="">
              <template #body="{ data }">
                <Button
                  label="Открыть урок"
                  icon="pi pi-book"
                  text
                  size="small"
                  @click="$router.push(`/my-lessons/${data.id}`)"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <Card v-if="pendingHomework.length">
        <template #title>Невыполненные задания</template>
        <template #content>
          <div v-for="lesson in pendingHomework" :key="lesson.id" class="pending-row">
            <span>
              <strong>{{ formatDateTime(lesson.scheduled_at) }}</strong>
              <template v-if="lesson.topic"> — {{ lesson.topic }}</template>
            </span>
            <Tag
              :value="`${lesson.homeworks.filter((h) => !h.is_done).length} задани${lesson.homeworks.filter((h) => !h.is_done).length === 1 ? 'е' : 'я'}`"
              severity="warn"
            />
            <Button
              label="Сделать"
              icon="pi pi-arrow-right"
              size="small"
              @click="$router.push(`/my-lessons/${lesson.id}`)"
            />
          </div>
        </template>
      </Card>

      <Card v-if="progress && progress.words_total">
        <template #title>Мой прогресс</template>
        <template #content>
          <div class="progress-grid">
            <div class="stat">
              <span class="stat-num">🔥 {{ progress.study_streak }}</span>
              <span class="stat-label">дней подряд</span>
            </div>
            <div class="stat">
              <span class="stat-num">{{ progress.words_learned }} / {{ progress.words_total }}</span>
              <span class="stat-label">слов выучено</span>
            </div>
            <div class="stat">
              <span class="stat-num">{{ progress.due_today }}</span>
              <span class="stat-label">к повтору сегодня</span>
            </div>
          </div>
          <Button
            v-if="progress.due_today"
            :label="`Повторить ${progress.due_today}`"
            icon="pi pi-bolt"
            class="review-btn"
            @click="$router.push('/study/today')"
          />
        </template>
      </Card>

      <Card v-if="cardSets.length">
        <template #title>Карточки для запоминания</template>
        <template #content>
          <div v-for="s in cardSets" :key="s.id" class="set-row">
            <span class="set-title">{{ s.title }}</span>
            <Tag
              v-if="s.due_count"
              :value="`${s.due_count} к повтору`"
              severity="warn"
            />
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
          <DataTable
            :value="past"
            selection-mode="single"
            @row-select="(e) => $router.push(`/my-lessons/${e.data.id}`)"
          >
            <template #empty>Проведённых уроков пока нет</template>
            <Column header="Когда">
              <template #body="{ data }">{{ formatDateTime(data.scheduled_at) }}</template>
            </Column>
            <Column field="topic" header="Что проходили" />
            <Column header="">
              <template #body="{ data }">
                <Button
                  label="Открыть урок"
                  icon="pi pi-book"
                  text
                  size="small"
                  @click="$router.push(`/my-lessons/${data.id}`)"
                />
              </template>
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
.progress-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 1rem;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.stat-num {
  font-size: 1.5rem;
  font-weight: 700;
}
.stat-label {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
.review-btn {
  margin-top: 0.25rem;
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
  flex: 1;
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
