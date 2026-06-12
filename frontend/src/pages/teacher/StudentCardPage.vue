<script setup lang="ts">
import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Card from "primevue/card";
import Checkbox from "primevue/checkbox";
import Chip from "primevue/chip";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import DatePicker from "primevue/datepicker";
import Dialog from "primevue/dialog";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Tab from "primevue/tab";
import TabList from "primevue/tablist";
import TabPanel from "primevue/tabpanel";
import TabPanels from "primevue/tabpanels";
import Tabs from "primevue/tabs";
import Tag from "primevue/tag";
import Textarea from "primevue/textarea";
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import {
  addComment,
  addHomework,
  addPayment,
  conductLesson,
  createLesson,
  createParent,
  createScheduleSlot,
  deleteHomework,
  deleteLesson,
  deleteScheduleSlot,
  getStudent,
  listComments,
  listLessons,
  listParents,
  listSchedule,
  listTransactions,
  revertLesson,
  savePrivateNote,
  setStudentPassword,
  updateHomework,
  updateLesson,
  updateParent,
} from "../../api";
import type {
  Comment,
  Lesson,
  Parent,
  ScheduleSlot,
  Student,
  Transaction,
} from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import LessonDialog from "../../components/LessonDialog.vue";
import { formatDateTime, formatMoney } from "../../utils/format";

const route = useRoute();
const toast = useToast();
const confirm = useConfirm();
const studentId = Number(route.params.id);

const student = ref<Student | null>(null);
const lessons = ref<Lesson[]>([]);
const parents = ref<Parent[]>([]);
const comments = ref<Comment[]>([]);
const transactions = ref<Transaction[]>([]);

// уроки
const lessonDialogOpen = ref(false);
const editingLesson = ref<Lesson | null>(null);
// повторяющееся расписание
const slots = ref<ScheduleSlot[]>([]);
const newSlotDay = ref<number | null>(null);
const newSlotTime = ref<Date | null>(null);
const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const weekdayOptions = WEEKDAYS.map((label, value) => ({ label, value }));
// ДЗ
const homeworkLesson = ref<Lesson | null>(null);
const homeworkText = ref("");
// родитель
const parentForm = ref({ email: "", full_name: "", lesson_price: 0, recommendations: "" });
// финансы
const paymentAmount = ref<number | null>(null);
const paymentComment = ref("");
// прочее
const newComment = ref("");
const privateNote = ref("");
const newPassword = ref("");

function showError(e: unknown, fallback: string) {
  const detail =
    (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
  toast.add({ severity: "error", summary: "Ошибка", detail, life: 4000 });
}

async function loadAll() {
  student.value = await getStudent(studentId);
  privateNote.value = student.value.teacher_private_note ?? "";
  [lessons.value, parents.value, comments.value, transactions.value, slots.value] =
    await Promise.all([
      listLessons(studentId),
      listParents(studentId),
      listComments(studentId),
      listTransactions(studentId),
      listSchedule(studentId),
    ]);
  const p = parents.value[0];
  if (p) {
    parentForm.value = {
      email: p.user.email,
      full_name: p.user.full_name,
      lesson_price: parseFloat(p.lesson_price),
      recommendations: p.recommendations ?? "",
    };
  }
}

onMounted(loadAll);

// --- повторяющееся расписание ---

async function onAddSlot() {
  if (newSlotDay.value === null || !newSlotTime.value) return;
  const hh = String(newSlotTime.value.getHours()).padStart(2, "0");
  const mm = String(newSlotTime.value.getMinutes()).padStart(2, "0");
  try {
    await createScheduleSlot(studentId, newSlotDay.value, `${hh}:${mm}`);
    newSlotDay.value = null;
    newSlotTime.value = null;
    [slots.value, lessons.value] = await Promise.all([
      listSchedule(studentId),
      listLessons(studentId),
    ]);
    toast.add({
      severity: "success",
      summary: "Слот добавлен",
      detail: "Уроки созданы на месяц вперёд",
      life: 4000,
    });
  } catch (e) {
    showError(e, "Не удалось добавить слот");
  }
}

async function onRemoveSlot(slot: ScheduleSlot) {
  confirm.require({
    message: `Удалить слот ${WEEKDAYS[slot.weekday]} ${slot.start_time.slice(0, 5)}? Будущие незатронутые уроки серии будут удалены.`,
    header: "Подтверждение",
    acceptLabel: "Удалить",
    rejectLabel: "Отмена",
    acceptProps: { severity: "danger" },
    accept: async () => {
      try {
        await deleteScheduleSlot(slot.id);
        [slots.value, lessons.value] = await Promise.all([
          listSchedule(studentId),
          listLessons(studentId),
        ]);
      } catch (e) {
        showError(e, "Не удалось удалить слот");
      }
    },
  });
}

// --- уроки ---

function openCreateLesson() {
  editingLesson.value = null;
  lessonDialogOpen.value = true;
}

function openEditLesson(lesson: Lesson) {
  editingLesson.value = lesson;
  lessonDialogOpen.value = true;
}

async function saveLesson(data: {
  scheduled_at: string;
  topic?: string;
  zoom_link?: string;
  recommendation?: string;
}) {
  try {
    if (editingLesson.value) {
      await updateLesson(editingLesson.value.id, data);
    } else {
      await createLesson(studentId, data);
    }
    lessonDialogOpen.value = false;
    lessons.value = await listLessons(studentId);
  } catch (e) {
    showError(e, "Не удалось сохранить урок");
  }
}

async function onConduct(lesson: Lesson) {
  try {
    await conductLesson(lesson.id);
    [lessons.value, transactions.value] = await Promise.all([
      listLessons(studentId),
      listTransactions(studentId),
    ]);
    toast.add({ severity: "success", summary: "Урок проведён, оплата начислена", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось отметить урок");
  }
}

async function onRevert(lesson: Lesson) {
  try {
    await revertLesson(lesson.id);
    [lessons.value, transactions.value] = await Promise.all([
      listLessons(studentId),
      listTransactions(studentId),
    ]);
  } catch (e) {
    showError(e, "Не удалось откатить урок");
  }
}

function onDeleteLesson(lesson: Lesson) {
  confirm.require({
    message: "Удалить урок?",
    header: "Подтверждение",
    acceptLabel: "Удалить",
    rejectLabel: "Отмена",
    acceptProps: { severity: "danger" },
    accept: async () => {
      try {
        await deleteLesson(lesson.id);
        lessons.value = await listLessons(studentId);
      } catch (e) {
        showError(e, "Не удалось удалить урок");
      }
    },
  });
}

// --- ДЗ ---

async function onAddHomework() {
  if (!homeworkLesson.value || !homeworkText.value.trim()) return;
  try {
    await addHomework(homeworkLesson.value.id, homeworkText.value.trim());
    homeworkText.value = "";
    homeworkLesson.value = null;
    lessons.value = await listLessons(studentId);
  } catch (e) {
    showError(e, "Не удалось добавить задание");
  }
}

async function onToggleHomework(id: number, is_done: boolean) {
  await updateHomework(id, { is_done });
  lessons.value = await listLessons(studentId);
}

async function onDeleteHomework(id: number) {
  await deleteHomework(id);
  lessons.value = await listLessons(studentId);
}

// --- родитель ---

async function saveParent() {
  try {
    const p = parents.value[0];
    if (p) {
      await updateParent(p.id, {
        full_name: parentForm.value.full_name,
        lesson_price: String(parentForm.value.lesson_price ?? 0),
        recommendations: parentForm.value.recommendations,
      });
      toast.add({ severity: "success", summary: "Карточка родителя обновлена", life: 3000 });
    } else {
      await createParent(studentId, {
        email: parentForm.value.email,
        full_name: parentForm.value.full_name,
        lesson_price: String(parentForm.value.lesson_price ?? 0),
        recommendations: parentForm.value.recommendations || undefined,
      });
      toast.add({
        severity: "success",
        summary: "Карточка родителя создана",
        detail: "Логин и пароль отправлены на почту",
        life: 4000,
      });
    }
    parents.value = await listParents(studentId);
  } catch (e) {
    showError(e, "Не удалось сохранить карточку родителя");
  }
}

// --- финансы ---

async function onAddPayment() {
  if (!paymentAmount.value) return;
  try {
    await addPayment(studentId, String(paymentAmount.value), paymentComment.value || undefined);
    paymentAmount.value = null;
    paymentComment.value = "";
    transactions.value = await listTransactions(studentId);
    toast.add({ severity: "success", summary: "Оплата внесена", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось внести оплату");
  }
}

// --- комментарии, заметка, пароль ---

async function onAddComment() {
  if (!newComment.value.trim()) return;
  await addComment(studentId, newComment.value.trim());
  newComment.value = "";
  comments.value = await listComments(studentId);
}

async function onSaveNote() {
  await savePrivateNote(studentId, privateNote.value || null);
  toast.add({ severity: "success", summary: "Заметка сохранена", life: 3000 });
}

async function onSetPassword() {
  if (!newPassword.value) return;
  try {
    await setStudentPassword(studentId, newPassword.value);
    newPassword.value = "";
    toast.add({ severity: "success", summary: "Пароль изменён", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось изменить пароль");
  }
}
</script>

<template>
  <AppLayout>
    <Card>
      <template #title>
        {{ student?.user.full_name ?? "…" }}
        <span class="email">{{ student?.user.email }}</span>
      </template>
      <template #content>
        <Tabs value="lessons">
          <TabList>
            <Tab value="lessons">Уроки</Tab>
            <Tab value="finance">Финансы</Tab>
            <Tab value="parent">Родитель</Tab>
            <Tab value="comments">Комментарии</Tab>
            <Tab value="note">Личная заметка</Tab>
            <Tab value="settings">Доступ</Tab>
          </TabList>
          <TabPanels>
            <!-- Уроки + ДЗ -->
            <TabPanel value="lessons">
              <div class="slots-box">
                <span class="slots-label">Регулярное расписание:</span>
                <Chip
                  v-for="s in slots"
                  :key="s.id"
                  :label="`${WEEKDAYS[s.weekday]} ${s.start_time.slice(0, 5)}`"
                  removable
                  @remove="onRemoveSlot(s)"
                />
                <span v-if="!slots.length" class="slots-empty">нет</span>
                <Select
                  v-model="newSlotDay"
                  :options="weekdayOptions"
                  option-label="label"
                  option-value="value"
                  placeholder="День"
                  size="small"
                  class="slot-day"
                />
                <DatePicker
                  v-model="newSlotTime"
                  time-only
                  hour-format="24"
                  placeholder="Время"
                  size="small"
                  class="slot-time"
                />
                <Button
                  label="Добавить"
                  icon="pi pi-plus"
                  size="small"
                  :disabled="newSlotDay === null || !newSlotTime"
                  @click="onAddSlot"
                />
              </div>
              <Button label="Новый урок" icon="pi pi-plus" class="mb" @click="openCreateLesson" />
              <DataTable :value="lessons" data-key="id">
                <template #empty>Уроков пока нет</template>
                <Column header="Когда">
                  <template #body="{ data }">{{ formatDateTime(data.scheduled_at) }}</template>
                </Column>
                <Column field="topic" header="Тема" />
                <Column header="Статус">
                  <template #body="{ data }">
                    <Tag
                      :value="
                        data.status === 'conducted'
                          ? 'Проведён'
                          : data.status === 'cancelled'
                            ? 'Отменён'
                            : 'Запланирован'
                      "
                      :severity="
                        data.status === 'conducted'
                          ? 'success'
                          : data.status === 'cancelled'
                            ? 'danger'
                            : 'info'
                      "
                    />
                  </template>
                </Column>
                <Column header="ДЗ">
                  <template #body="{ data }">
                    <div v-for="hw in data.homeworks" :key="hw.id" class="hw-row">
                      <Checkbox
                        :model-value="hw.is_done"
                        binary
                        @update:model-value="(v: boolean) => onToggleHomework(hw.id, v)"
                      />
                      <span :class="{ done: hw.is_done }">{{ hw.description }}</span>
                      <Button
                        icon="pi pi-times"
                        text
                        rounded
                        size="small"
                        severity="danger"
                        @click="onDeleteHomework(hw.id)"
                      />
                    </div>
                    <Button
                      label="Добавить ДЗ"
                      icon="pi pi-plus"
                      text
                      size="small"
                      @click="homeworkLesson = data"
                    />
                  </template>
                </Column>
                <Column header="Действия">
                  <template #body="{ data }">
                    <div class="actions">
                      <Button
                        v-if="data.status === 'planned'"
                        v-tooltip="'Урок проведён'"
                        icon="pi pi-check"
                        severity="success"
                        text
                        rounded
                        @click="onConduct(data)"
                      />
                      <Button
                        v-if="data.status === 'conducted'"
                        v-tooltip="'Откатить проведение'"
                        icon="pi pi-undo"
                        severity="warn"
                        text
                        rounded
                        @click="onRevert(data)"
                      />
                      <Button icon="pi pi-pencil" text rounded @click="openEditLesson(data)" />
                      <Button
                        icon="pi pi-trash"
                        severity="danger"
                        text
                        rounded
                        @click="onDeleteLesson(data)"
                      />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </TabPanel>

            <!-- Финансы -->
            <TabPanel value="finance">
              <div class="payment-form">
                <InputNumber
                  v-model="paymentAmount"
                  placeholder="Сумма"
                  :min="0"
                  mode="currency"
                  currency="RUB"
                  locale="ru-RU"
                />
                <InputText v-model="paymentComment" placeholder="Комментарий (необязательно)" />
                <Button label="Внести оплату" icon="pi pi-wallet" @click="onAddPayment" />
              </div>
              <DataTable :value="transactions">
                <template #empty>Операций пока нет</template>
                <Column header="Дата">
                  <template #body="{ data }">{{ formatDateTime(data.created_at) }}</template>
                </Column>
                <Column header="Тип">
                  <template #body="{ data }">
                    <Tag
                      :value="data.type === 'charge' ? 'Начисление' : 'Оплата'"
                      :severity="data.type === 'charge' ? 'warn' : 'success'"
                    />
                  </template>
                </Column>
                <Column header="Сумма">
                  <template #body="{ data }">{{ formatMoney(data.amount) }}</template>
                </Column>
                <Column field="comment" header="Комментарий" />
              </DataTable>
            </TabPanel>

            <!-- Родитель -->
            <TabPanel value="parent">
              <form class="form" @submit.prevent="saveParent">
                <label>
                  Имя родителя
                  <InputText v-model="parentForm.full_name" required fluid />
                </label>
                <label>
                  Почта {{ parents.length ? "" : "(туда придут логин и пароль)" }}
                  <InputText
                    v-model="parentForm.email"
                    type="email"
                    required
                    :disabled="parents.length > 0"
                    fluid
                  />
                </label>
                <label>
                  Стоимость урока, ₽
                  <InputNumber v-model="parentForm.lesson_price" :min="0" fluid />
                </label>
                <label>
                  Рекомендации для родителя
                  <Textarea v-model="parentForm.recommendations" rows="4" fluid />
                </label>
                <Button
                  type="submit"
                  :label="parents.length ? 'Сохранить' : 'Создать карточку родителя'"
                />
              </form>
            </TabPanel>

            <!-- Комментарии -->
            <TabPanel value="comments">
              <div v-for="c in comments" :key="c.id" class="comment">
                <strong>{{ c.author_name }}</strong>
                <span class="comment-date">{{ formatDateTime(c.created_at) }}</span>
                <p>{{ c.body }}</p>
              </div>
              <p v-if="!comments.length">Комментариев пока нет</p>
              <div class="comment-form">
                <Textarea v-model="newComment" rows="2" placeholder="Новый комментарий" fluid />
                <Button label="Отправить" @click="onAddComment" />
              </div>
            </TabPanel>

            <!-- Личная заметка -->
            <TabPanel value="note">
              <p class="hint">Заметку видите только вы. Ученику и родителю она недоступна.</p>
              <Textarea v-model="privateNote" rows="6" fluid />
              <Button label="Сохранить" class="mt" @click="onSaveNote" />
            </TabPanel>

            <!-- Доступ -->
            <TabPanel value="settings">
              <form class="form" @submit.prevent="onSetPassword">
                <label>
                  Новый пароль ученика
                  <InputText v-model="newPassword" required fluid />
                </label>
                <Button type="submit" label="Сменить пароль" severity="warn" />
              </form>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </template>
    </Card>

    <LessonDialog
      v-model:visible="lessonDialogOpen"
      :lesson="editingLesson"
      @save="saveLesson"
    />

    <Dialog
      :visible="homeworkLesson !== null"
      header="Новое домашнее задание"
      modal
      @update:visible="homeworkLesson = null"
    >
      <form class="form" @submit.prevent="onAddHomework">
        <Textarea v-model="homeworkText" rows="3" placeholder="Что задано" fluid />
        <Button type="submit" label="Добавить" :disabled="!homeworkText.trim()" />
      </form>
    </Dialog>
  </AppLayout>
</template>

<style scoped>
.email {
  margin-left: 0.75rem;
  font-size: 0.9rem;
  font-weight: 400;
  color: var(--p-text-muted-color);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 28rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}
.mb {
  margin-bottom: 1rem;
}
.slots-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--p-surface-100);
  border-radius: 8px;
}
.slots-label {
  font-weight: 600;
  font-size: 0.9rem;
}
.slots-empty {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
.slot-day {
  width: 7rem;
  margin-left: auto;
}
.slot-time {
  width: 7rem;
}
.mt {
  margin-top: 1rem;
}
.hw-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.done {
  text-decoration: line-through;
  color: var(--p-text-muted-color);
}
.actions {
  display: flex;
  gap: 0.25rem;
}
.payment-form {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
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
  max-width: 28rem;
}
.hint {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
</style>
