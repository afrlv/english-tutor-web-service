<script setup lang="ts">
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Tag from "primevue/tag";
import { computed, onMounted, ref } from "vue";

import { financeSummary, listLessons, listStudents } from "../../api";
import type { Lesson, Student } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { formatMoney } from "../../utils/format";

interface TodayLesson extends Lesson {
  student_name: string;
}

const todayLessons = ref<TodayLesson[]>([]);
const totalEarned = ref("0");
const loading = ref(true);

const today = computed(() =>
  new Date().toLocaleDateString("ru-RU", { day: "numeric", month: "long", weekday: "long" }),
);

function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

onMounted(async () => {
  try {
    const [students, summary] = await Promise.all([listStudents(), financeSummary()]);
    totalEarned.value = summary.total_earned;
    const byStudent = await Promise.all(
      students.map(async (s: Student) => {
        const lessons = await listLessons(s.id);
        return lessons
          .filter((l) => isToday(l.scheduled_at) && l.status !== "cancelled")
          .map((l) => ({ ...l, student_name: s.user.full_name }));
      }),
    );
    todayLessons.value = byStudent
      .flat()
      .sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at));
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <AppLayout>
    <div class="cards">
      <Card>
        <template #title>Уроки сегодня — {{ today }}</template>
        <template #content>
          <DataTable :value="todayLessons" :loading="loading">
            <template #empty>Сегодня уроков нет</template>
            <Column header="Время">
              <template #body="{ data }">
                {{ new Date(data.scheduled_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }) }}
              </template>
            </Column>
            <Column field="student_name" header="Ученик" />
            <Column field="topic" header="Тема" />
            <Column header="Статус">
              <template #body="{ data }">
                <Tag
                  :value="data.status === 'conducted' ? 'Проведён' : 'Запланирован'"
                  :severity="data.status === 'conducted' ? 'success' : 'info'"
                />
              </template>
            </Column>
            <Column header="Zoom">
              <template #body="{ data }">
                <a v-if="data.zoom_link" :href="data.zoom_link" target="_blank">Ссылка</a>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
      <Card>
        <template #title>Заработано всего</template>
        <template #content>
          <span class="total">{{ formatMoney(totalEarned) }}</span>
        </template>
      </Card>
    </div>
  </AppLayout>
</template>

<style scoped>
.cards {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.total {
  font-size: 2rem;
  font-weight: 600;
}
</style>
