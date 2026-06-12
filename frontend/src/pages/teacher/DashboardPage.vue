<script setup lang="ts">
import type { CalendarOptions, EventClickArg } from "@fullcalendar/core";
import ruLocale from "@fullcalendar/core/locales/ru";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin, { type DateClickArg } from "@fullcalendar/interaction";
import timeGridPlugin from "@fullcalendar/timegrid";
import FullCalendar from "@fullcalendar/vue3";
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import Tag from "primevue/tag";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import {
  cancelLesson,
  conductLesson,
  createLesson,
  deleteLesson,
  financeSummary,
  listAllLessons,
  listStudents,
  restoreLesson,
  revertLesson,
  updateLesson,
} from "../../api";
import type { CalendarLesson, FinanceSummary, Student } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import BalanceCell from "../../components/BalanceCell.vue";
import CancelLessonDialog, { type CancelKind } from "../../components/CancelLessonDialog.vue";
import LessonDialog from "../../components/LessonDialog.vue";
import { formatDateTime, formatMoney } from "../../utils/format";
import { cancellationLabels, statusLabel, statusSeverity } from "../../utils/lessons";

const router = useRouter();
const toast = useToast();
const summary = ref<FinanceSummary | null>(null);
const loading = ref(true);
const students = ref<Student[]>([]);
const calendarRef = ref<InstanceType<typeof FullCalendar> | null>(null);
const dialogOpen = ref(false);
const clickedDate = ref<Date | null>(null);
// Модалка деталей урока (клик по событию в календаре)
const selectedLesson = ref<CalendarLesson | null>(null);
const editingLesson = ref<CalendarLesson | null>(null);
const acting = ref(false);
const cancelOpen = ref(false);

// Цвета событий по статусу урока
const statusColors: Record<string, string> = {
  planned: "var(--p-blue-500)",
  conducted: "var(--p-green-500)",
  cancelled: "var(--p-surface-400)",
};

const calendarOptions = ref<CalendarOptions>({
  plugins: [timeGridPlugin, dayGridPlugin, interactionPlugin],
  initialView: "timeGridWeek",
  locale: ruLocale,
  headerToolbar: {
    left: "prev,next today",
    center: "title",
    right: "timeGridWeek,dayGridMonth",
  },
  height: "auto",
  nowIndicator: true,
  // Видимый диапазон рабочего дня; scrollTime — куда проскроллено при открытии
  slotMinTime: "07:00:00",
  slotMaxTime: "23:00:00",
  scrollTime: "09:00:00",
  allDaySlot: false,
  // FullCalendar сам запрашивает уроки под видимый диапазон при листании
  events: async (info, success, failure) => {
    try {
      const lessons = await listAllLessons(info.start.toISOString(), info.end.toISOString());
      success(
        lessons.map((l) => ({
          id: String(l.id),
          title: l.topic ? `${l.student_name}: ${l.topic}` : l.student_name,
          start: l.scheduled_at,
          color: statusColors[l.status],
          extendedProps: { lesson: l },
        })),
      );
    } catch (e) {
      failure(e as Error);
    }
  },
  // Урок — час по умолчанию (длительность не храним)
  defaultTimedEventDuration: "01:00",
  forceEventDuration: true,
  eventClick: (arg: EventClickArg) => {
    selectedLesson.value = arg.event.extendedProps.lesson as CalendarLesson;
  },
  // Клик по свободному слоту — новый урок на это время
  dateClick: (arg: DateClickArg) => {
    const date = new Date(arg.date);
    if (arg.allDay) date.setHours(12, 0, 0, 0); // в месячной сетке времени нет
    clickedDate.value = date;
    dialogOpen.value = true;
  },
});

function openCreate() {
  clickedDate.value = null;
  editingLesson.value = null;
  dialogOpen.value = true;
}

function openEdit() {
  editingLesson.value = selectedLesson.value;
  selectedLesson.value = null;
  dialogOpen.value = true;
}

function showError(e: unknown, fallback: string) {
  const detail =
    (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
  toast.add({ severity: "error", summary: "Ошибка", detail, life: 4000 });
}

async function refresh() {
  calendarRef.value?.getApi().refetchEvents();
  summary.value = await financeSummary();
}

async function saveLesson(
  data: { scheduled_at: string; topic?: string; zoom_link?: string; recommendation?: string },
  studentId: number | null,
) {
  try {
    if (editingLesson.value) {
      await updateLesson(editingLesson.value.id, data);
    } else {
      if (studentId === null) return;
      await createLesson(studentId, data);
    }
    dialogOpen.value = false;
    editingLesson.value = null;
    await refresh();
    toast.add({ severity: "success", summary: "Урок сохранён", life: 3000 });
  } catch (e: unknown) {
    showError(e, "Не удалось сохранить урок");
  }
}

async function onConduct() {
  if (!selectedLesson.value) return;
  acting.value = true;
  try {
    await conductLesson(selectedLesson.value.id);
    selectedLesson.value = null;
    await refresh();
    toast.add({ severity: "success", summary: "Урок проведён, оплата начислена", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось отметить урок");
  } finally {
    acting.value = false;
  }
}

async function onRevert() {
  if (!selectedLesson.value) return;
  acting.value = true;
  try {
    await revertLesson(selectedLesson.value.id);
    selectedLesson.value = null;
    await refresh();
  } catch (e) {
    showError(e, "Не удалось откатить урок");
  } finally {
    acting.value = false;
  }
}

async function onCancelConfirm(
  kind: CancelKind,
  comment: string | null,
  chargeAmount: string | null,
) {
  if (!selectedLesson.value) return;
  acting.value = true;
  try {
    await cancelLesson(selectedLesson.value.id, kind, comment, chargeAmount);
    cancelOpen.value = false;
    selectedLesson.value = null;
    await refresh();
    toast.add({
      severity: "success",
      summary: kind === "late" ? "Урок отменён, оплата начислена" : "Урок отменён",
      life: 3000,
    });
  } catch (e) {
    showError(e, "Не удалось отменить урок");
  } finally {
    acting.value = false;
  }
}

async function onRestore() {
  if (!selectedLesson.value) return;
  acting.value = true;
  try {
    await restoreLesson(selectedLesson.value.id);
    selectedLesson.value = null;
    await refresh();
    toast.add({ severity: "success", summary: "Урок восстановлен", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось восстановить урок");
  } finally {
    acting.value = false;
  }
}

async function onDelete() {
  if (!selectedLesson.value) return;
  acting.value = true;
  try {
    await deleteLesson(selectedLesson.value.id);
    selectedLesson.value = null;
    await refresh();
    toast.add({ severity: "success", summary: "Урок удалён", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось удалить урок");
  } finally {
    acting.value = false;
  }
}

function toStudentCard() {
  if (selectedLesson.value) router.push(`/students/${selectedLesson.value.student_id}`);
}

onMounted(async () => {
  try {
    [summary.value, students.value] = await Promise.all([financeSummary(), listStudents()]);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <AppLayout>
    <div class="cards">
      <Card>
        <template #title>Заработано всего</template>
        <template #content>
          <span class="total">{{ formatMoney(summary?.total_earned ?? 0) }}</span>
        </template>
      </Card>

      <Card>
        <template #title>
          <div class="schedule-header">
            Расписание
            <Button label="Новый урок" icon="pi pi-plus" size="small" @click="openCreate" />
          </div>
        </template>
        <template #content>
          <FullCalendar ref="calendarRef" :options="calendarOptions" />
          <div class="legend">
            <span><i class="dot planned" /> Запланирован</span>
            <span><i class="dot conducted" /> Проведён</span>
            <span><i class="dot cancelled" /> Отменён</span>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Финансы по ученикам</template>
        <template #content>
          <DataTable
            :value="summary?.students ?? []"
            :loading="loading"
            selection-mode="single"
            @row-select="(e) => router.push(`/students/${e.data.student_id}`)"
          >
            <template #empty>Пока нет данных</template>
            <Column field="student_name" header="Ученик" />
            <Column header="Заработано">
              <template #body="{ data }">{{ formatMoney(data.earned) }}</template>
            </Column>
            <Column header="Оплачено">
              <template #body="{ data }">{{ formatMoney(data.paid) }}</template>
            </Column>
            <Column header="Баланс">
              <template #body="{ data }">
                <BalanceCell :debt="data.debt" :lesson-price="data.lesson_price" />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </div>

    <LessonDialog
      v-model:visible="dialogOpen"
      :lesson="editingLesson"
      :students="students"
      :initial-date="clickedDate"
      @save="saveLesson"
    />

    <Dialog
      :visible="selectedLesson !== null"
      :header="selectedLesson?.student_name"
      modal
      class="lesson-modal"
      @update:visible="selectedLesson = null"
    >
      <template v-if="selectedLesson">
        <div class="detail">
          <div class="row">
            <span class="label">Когда</span>
            <span>{{ formatDateTime(selectedLesson.scheduled_at) }}</span>
          </div>
          <div class="row">
            <span class="label">Статус</span>
            <Tag
              :value="statusLabel(selectedLesson.status)"
              :severity="statusSeverity(selectedLesson.status)"
            />
          </div>
          <div v-if="selectedLesson.cancellation_kind" class="row">
            <span class="label">Причина</span>
            <span>
              {{ cancellationLabels[selectedLesson.cancellation_kind] }}
              <template v-if="selectedLesson.cancellation_comment">
                — {{ selectedLesson.cancellation_comment }}
              </template>
            </span>
          </div>
          <div v-if="selectedLesson.rescheduled_from" class="row">
            <span class="label">Перенесён с</span>
            <span>{{ formatDateTime(selectedLesson.rescheduled_from) }}</span>
          </div>
          <div v-if="selectedLesson.topic" class="row">
            <span class="label">Тема</span>
            <span>{{ selectedLesson.topic }}</span>
          </div>
          <div v-if="selectedLesson.zoom_link" class="row">
            <span class="label">Zoom</span>
            <a :href="selectedLesson.zoom_link" target="_blank">Подключиться</a>
          </div>
          <div v-if="selectedLesson.recommendation" class="row">
            <span class="label">Рекомендации</span>
            <span>{{ selectedLesson.recommendation }}</span>
          </div>
        </div>
        <div class="modal-actions">
          <Button
            v-if="selectedLesson.status === 'planned'"
            label="Проведён"
            icon="pi pi-check"
            severity="success"
            :loading="acting"
            @click="onConduct"
          />
          <Button
            v-if="selectedLesson.status === 'conducted'"
            label="Откатить"
            icon="pi pi-undo"
            severity="warn"
            :loading="acting"
            @click="onRevert"
          />
          <Button
            v-if="selectedLesson.status === 'planned'"
            label="Отменить"
            icon="pi pi-ban"
            severity="warn"
            outlined
            @click="cancelOpen = true"
          />
          <Button
            v-if="selectedLesson.status === 'cancelled'"
            label="Восстановить"
            icon="pi pi-replay"
            severity="success"
            outlined
            :loading="acting"
            @click="onRestore"
          />
          <Button label="Изменить" icon="pi pi-pencil" severity="secondary" @click="openEdit" />
          <Button
            label="Удалить"
            icon="pi pi-trash"
            severity="danger"
            outlined
            :loading="acting"
            @click="onDelete"
          />
          <Button
            label="Карточка ученика"
            icon="pi pi-user"
            text
            @click="toStudentCard"
          />
        </div>
      </template>
    </Dialog>

    <CancelLessonDialog v-model:visible="cancelOpen" @confirm="onCancelConfirm" />
  </AppLayout>
</template>

<style scoped>
.cards {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detail {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  min-width: 22rem;
}
.row {
  display: flex;
  gap: 0.75rem;
}
.label {
  width: 8rem;
  flex-shrink: 0;
  color: var(--p-text-muted-color);
}
.modal-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 1.25rem;
}
.total {
  font-size: 2rem;
  font-weight: 600;
}
.debt {
  color: var(--p-red-500);
  font-weight: 600;
}
.legend {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
.dot {
  display: inline-block;
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
  margin-right: 0.3rem;
}
.dot.planned {
  background: var(--p-blue-500);
}
.dot.conducted {
  background: var(--p-green-500);
}
.dot.cancelled {
  background: var(--p-surface-400);
}
</style>

<style>
/* FullCalendar: события кликабельны */
.fc-event {
  cursor: pointer;
}
</style>
