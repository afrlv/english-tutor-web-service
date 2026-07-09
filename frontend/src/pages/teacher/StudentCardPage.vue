<script setup lang="ts">
import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Card from "primevue/card";
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
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  addComment,
  addPayment,
  attachParent,
  conductLesson,
  createCardSet,
  createLesson,
  createParent,
  createScheduleSlot,
  listTeacherParents,
  copyCardSet,
  deleteCardSet,
  getCardSet,
  deleteScheduleSlot,
  getStudent,
  type LessonInput,
  listCardSets,
  listComments,
  listLessons,
  listParents,
  listSchedule,
  listTransactions,
  revertLesson,
  savePrivateNote,
  setStudentPassword,
  updateLesson,
  updateParent,
  updateStudent,
} from "../../api";
import type {
  CardSet,
  CardSetSummary,
  Comment,
  Homework,
  Lesson,
  Parent,
  ScheduleSlot,
  Student,
  TeacherParent,
  Transaction,
} from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import AttachmentList from "../../components/AttachmentList.vue";
import BalanceCell from "../../components/BalanceCell.vue";
import CardSetEditor from "../../components/CardSetEditor.vue";
import LessonDialog from "../../components/LessonDialog.vue";
import { formatDateTime, formatMoney } from "../../utils/format";
import { cancellationLabels, statusLabel, statusSeverity } from "../../utils/lessons";

const route = useRoute();
const router = useRouter();
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
const templateLesson = ref<Lesson | null>(null);
const lessonInitialDate = ref<Date | null>(null);
// профиль
const profileForm = ref({ full_name: "", default_zoom_link: "", birthday: null as Date | null });
// наборы карточек
const cardSets = ref<CardSetSummary[]>([]);
const openSet = ref<CardSet | null>(null);
const newSetTitle = ref("");
// повторяющееся расписание
const slots = ref<ScheduleSlot[]>([]);
const newSlotDay = ref<number | null>(null);
const newSlotTime = ref<Date | null>(null);
const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const weekdayOptions = WEEKDAYS.map((label, value) => ({ label, value }));
// родитель
const parentForm = ref({ email: "", full_name: "", lesson_price: 0, recommendations: "" });
// выбор существующего родителя (привязка второго ребёнка) и список родителей учителя
const existingParentId = ref<number | null>(null);
const teacherParents = ref<TeacherParent[]>([]);
// финансы
const paymentAmount = ref<number | null>(null);
const paymentComment = ref("");

const lessonPrice = computed(() => parseFloat(parents.value[0]?.lesson_price ?? "0"));
const parentSelectOptions = computed(() =>
  teacherParents.value.map((p) => ({
    label: `${p.full_name} (${p.email}) — ${p.children_count} реб.`,
    value: p.user_id,
  })),
);
// Список уроков: по возрастанию даты (ранняя сверху)
const sortedLessons = computed(() =>
  lessons.value.slice().sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at)),
);
// История занятий: проведённые уроки, новые сверху
const conductedLessons = computed(() =>
  lessons.value
    .filter((l) => l.status === "conducted")
    .slice()
    .sort((a, b) => b.scheduled_at.localeCompare(a.scheduled_at)),
);

const currentDebt = computed(() => {
  const charged = transactions.value
    .filter((t) => t.type === "charge")
    .reduce((s, t) => s + parseFloat(t.amount), 0);
  const paid = transactions.value
    .filter((t) => t.type === "payment")
    .reduce((s, t) => s + parseFloat(t.amount), 0);
  return charged - paid;
});

/** Абонемент: подставить стоимость N уроков в форму оплаты */
function fillPackage(lessonsCount: number) {
  if (!lessonPrice.value) return;
  paymentAmount.value = lessonsCount * lessonPrice.value;
  paymentComment.value = `Абонемент ${lessonsCount} ${lessonsCount === 4 ? "урока" : "уроков"}`;
}
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
  profileForm.value = {
    full_name: student.value.user.full_name,
    default_zoom_link: student.value.default_zoom_link ?? "",
    birthday: student.value.birthday ? new Date(student.value.birthday) : null,
  };
  [
    lessons.value,
    parents.value,
    comments.value,
    transactions.value,
    slots.value,
    cardSets.value,
    teacherParents.value,
  ] = await Promise.all([
    listLessons(studentId),
    listParents(studentId),
    listComments(studentId),
    listTransactions(studentId),
    listSchedule(studentId),
    listCardSets(studentId),
    listTeacherParents(),
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

// --- наборы карточек ---

async function onCreateSet() {
  if (!newSetTitle.value.trim()) return;
  try {
    const created = await createCardSet(studentId, newSetTitle.value.trim(), []);
    newSetTitle.value = "";
    cardSets.value = await listCardSets(studentId);
    openSet.value = created; // сразу открываем для наполнения
  } catch (e) {
    showError(e, "Не удалось создать набор");
  }
}

async function onOpenSet(setId: number) {
  openSet.value = await getCardSet(setId);
}

async function onSetChanged() {
  cardSets.value = await listCardSets(studentId);
}

function onDeleteSet(s: CardSetSummary) {
  confirm.require({
    message: `Удалить набор «${s.title}» (${s.total} карт.)?`,
    header: "Подтверждение",
    acceptLabel: "Удалить",
    rejectLabel: "Отмена",
    acceptProps: { severity: "danger" },
    accept: async () => {
      try {
        await deleteCardSet(s.id);
        cardSets.value = await listCardSets(studentId);
      } catch (e) {
        showError(e, "Не удалось удалить набор");
      }
    },
  });
}

async function onCopySet(setId: number) {
  try {
    await copyCardSet(setId);
    cardSets.value = await listCardSets(studentId);
    toast.add({ severity: "success", summary: "Набор скопирован", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось скопировать набор");
  }
}

// --- профиль ---

async function saveProfile() {
  try {
    const b = profileForm.value.birthday;
    const birthday = b
      ? `${b.getFullYear()}-${String(b.getMonth() + 1).padStart(2, "0")}-${String(b.getDate()).padStart(2, "0")}`
      : null;
    student.value = await updateStudent(studentId, {
      full_name: profileForm.value.full_name,
      default_zoom_link: profileForm.value.default_zoom_link.trim() || null,
      birthday,
    });
    // Смена постоянной ссылки обновляет будущие уроки — перезагружаем
    lessons.value = await listLessons(studentId);
    toast.add({ severity: "success", summary: "Профиль сохранён", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось сохранить профиль");
  }
}

// --- уроки ---

function openCreateLesson() {
  editingLesson.value = null;
  templateLesson.value = null;
  lessonInitialDate.value = null;
  lessonDialogOpen.value = true;
}

function openDuplicateLesson(lesson: Lesson) {
  // Дубликат: те же поля, время — через неделю
  editingLesson.value = null;
  templateLesson.value = lesson;
  lessonInitialDate.value = new Date(
    new Date(lesson.scheduled_at).getTime() + 7 * 24 * 3600 * 1000,
  );
  lessonDialogOpen.value = true;
}

async function saveLesson(data: LessonInput) {
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
    } else if (existingParentId.value !== null) {
      // привязать уже заведённого родителя (другого ученика) к этому ученику
      await attachParent(studentId, {
        parent_user_id: existingParentId.value,
        lesson_price: String(parentForm.value.lesson_price ?? 0),
        recommendations: parentForm.value.recommendations || undefined,
      });
      toast.add({ severity: "success", summary: "Родитель привязан", life: 3000 });
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
    existingParentId.value = null;
    [parents.value, teacherParents.value] = await Promise.all([
      listParents(studentId),
      listTeacherParents(),
    ]);
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
            <Tab value="history">История</Tab>
            <Tab value="finance">Финансы</Tab>
            <Tab value="parent">Родитель</Tab>
            <Tab value="cards">Карточки</Tab>
            <Tab value="comments">Комментарии</Tab>
            <Tab value="note">Личная заметка</Tab>
            <Tab value="profile">Профиль</Tab>
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
              <DataTable :value="sortedLessons" data-key="id">
                <template #empty>Уроков пока нет</template>
                <Column header="Когда">
                  <template #body="{ data }">
                    {{ formatDateTime(data.scheduled_at) }}
                    <i
                      v-if="data.rescheduled_from"
                      v-tooltip="`Перенесён с ${formatDateTime(data.rescheduled_from)}`"
                      class="pi pi-history rescheduled"
                    />
                  </template>
                </Column>
                <Column field="topic" header="Тема" />
                <Column header="Статус">
                  <template #body="{ data }">
                    <Tag
                      v-tooltip="
                        data.cancellation_kind
                          ? cancellationLabels[data.cancellation_kind as keyof typeof cancellationLabels]
                          : undefined
                      "
                      :value="statusLabel(data.status)"
                      :severity="statusSeverity(data.status)"
                    />
                  </template>
                </Column>
                <Column header="ДЗ">
                  <template #body="{ data }">
                    <span v-if="data.homeworks.length" class="hw-summary">
                      {{ data.homeworks.length }} задани{{ data.homeworks.length === 1 ? "е" : "я" }}
                      <i
                        v-if="data.homeworks.some((h: Homework) => h.grade)"
                        v-tooltip="'Есть оценки'"
                        class="pi pi-verified graded"
                      />
                    </span>
                  </template>
                </Column>
                <Column header="Действия">
                  <template #body="{ data }">
                    <div class="actions">
                      <Button
                        label="Открыть"
                        icon="pi pi-book"
                        text
                        size="small"
                        @click="router.push(`/lessons/${data.id}`)"
                      />
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
                      <Button
                        v-tooltip="'Продублировать на следующую неделю'"
                        icon="pi pi-copy"
                        text
                        rounded
                        @click="openDuplicateLesson(data)"
                      />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </TabPanel>

            <!-- История занятий: конспект проведённых уроков -->
            <TabPanel value="history">
              <p v-if="!conductedLessons.length" class="hint">
                Проведённых уроков пока нет — история появится после первого занятия.
              </p>
              <div v-for="l in conductedLessons" :key="l.id" class="feed-item">
                <div class="feed-head">
                  <strong>{{ formatDateTime(l.scheduled_at) }}</strong>
                  <span v-if="l.topic" class="feed-topic">{{ l.topic }}</span>
                  <Button
                    label="Открыть"
                    icon="pi pi-book"
                    text
                    size="small"
                    @click="router.push(`/lessons/${l.id}`)"
                  />
                </div>
                <p v-if="l.recommendation" class="feed-rec">{{ l.recommendation }}</p>
                <AttachmentList :attachments="l.attachments" />
                <div v-for="hw in l.homeworks" :key="hw.id" class="feed-hw">
                  <i :class="hw.is_done ? 'pi pi-check-circle done-icon' : 'pi pi-circle'" />
                  <span>{{ hw.description }}</span>
                  <Tag
                    v-if="hw.grade"
                    :value="String(hw.grade)"
                    :severity="hw.grade >= 4 ? 'success' : hw.grade === 3 ? 'warn' : 'danger'"
                  />
                </div>
              </div>
            </TabPanel>

            <!-- Финансы -->
            <TabPanel value="finance">
              <p class="balance-line">
                Баланс:
                <BalanceCell :debt="currentDebt" :lesson-price="lessonPrice" />
              </p>
              <div v-if="lessonPrice > 0" class="packages">
                <span class="packages-label">Абонемент:</span>
                <Button
                  v-for="n in [4, 8, 12]"
                  :key="n"
                  :label="`${n} ур. — ${(n * lessonPrice).toLocaleString('ru-RU')} ₽`"
                  size="small"
                  severity="secondary"
                  outlined
                  @click="fillPackage(n)"
                />
              </div>
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
                <label v-if="!parents.length && parentSelectOptions.length">
                  Привязать существующего родителя
                  <Select
                    v-model="existingParentId"
                    :options="parentSelectOptions"
                    option-label="label"
                    option-value="value"
                    placeholder="— завести нового —"
                    show-clear
                    fluid
                  />
                </label>
                <template v-if="existingParentId === null">
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
                </template>
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
                  :label="
                    parents.length
                      ? 'Сохранить'
                      : existingParentId !== null
                        ? 'Привязать родителя'
                        : 'Создать карточку родителя'
                  "
                />
              </form>
            </TabPanel>

            <!-- Наборы карточек -->
            <TabPanel value="cards">
              <div class="set-create">
                <InputText
                  v-model="newSetTitle"
                  placeholder="Название набора (напр. Unit 3: Food)"
                  fluid
                  @keyup.enter="onCreateSet"
                />
                <Button
                  label="Создать набор"
                  icon="pi pi-plus"
                  :disabled="!newSetTitle.trim()"
                  @click="onCreateSet"
                />
              </div>
              <div v-for="s in cardSets" :key="s.id" class="set-row">
                <span class="set-title">{{ s.title }}</span>
                <Tag
                  :value="`${s.learned} / ${s.total} выучено`"
                  :severity="s.total > 0 && s.learned === s.total ? 'success' : 'secondary'"
                />
                <Button
                  label="Открыть"
                  icon="pi pi-pencil"
                  text
                  size="small"
                  @click="onOpenSet(s.id)"
                />
                <Button
                  v-tooltip="'Создать копию набора'"
                  icon="pi pi-copy"
                  text
                  rounded
                  size="small"
                  @click="onCopySet(s.id)"
                />
                <Button
                  icon="pi pi-trash"
                  text
                  rounded
                  size="small"
                  severity="danger"
                  @click="onDeleteSet(s)"
                />
              </div>
              <p v-if="!cardSets.length" class="hint">
                Наборов пока нет. Создайте набор и наполните его словами — ученик
                увидит его в своём кабинете и сможет учить.
              </p>
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

            <!-- Профиль -->
            <TabPanel value="profile">
              <form class="form" @submit.prevent="saveProfile">
                <label>
                  Имя и фамилия
                  <InputText v-model="profileForm.full_name" required fluid />
                </label>
                <label>
                  День рождения (попадёт в утренний дайджест)
                  <DatePicker
                    v-model="profileForm.birthday"
                    date-format="dd.mm.yy"
                    show-icon
                    fluid
                  />
                </label>
                <label>
                  Постоянная ссылка Zoom (подставляется в новые уроки)
                  <InputText
                    v-model="profileForm.default_zoom_link"
                    placeholder="https://zoom.us/j/…"
                    fluid
                  />
                </label>
                <Button type="submit" label="Сохранить" />
              </form>
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
      :template="templateLesson"
      :initial-date="lessonInitialDate"
      @save="saveLesson"
    />

    <Dialog
      :visible="openSet !== null"
      :header="openSet?.title"
      modal
      class="set-dialog"
      @update:visible="openSet = null"
    >
      <CardSetEditor v-if="openSet" :card-set="openSet" @changed="onSetChanged" />
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
  gap: 0.25rem;
}
.hw-block {
  margin-bottom: 0.5rem;
}
.grade-select {
  width: 6.5rem;
}
.hw-form {
  min-width: 26rem;
}
.feed-item {
  padding: 0.85rem 0;
  border-bottom: 1px solid var(--p-surface-200);
}
.feed-head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.feed-topic {
  font-weight: 600;
  flex: 1;
}
.feed-rec {
  margin: 0.3rem 0;
  color: var(--p-text-muted-color);
  white-space: pre-wrap;
}
.feed-hw {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.3rem;
  font-size: 0.95rem;
}
.done-icon {
  color: var(--p-green-500);
}
.set-create {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  max-width: 32rem;
}
.set-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--p-surface-200);
}
.set-title {
  font-weight: 600;
  min-width: 12rem;
}
.attach-section {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}
.link-add {
  display: flex;
  gap: 0.5rem;
  width: 100%;
}
.link-add > :first-child {
  flex: 1;
}
.link-name {
  width: 9rem;
}
.hw-answer {
  margin: 0.25rem 0 0;
  font-size: 0.9rem;
  font-style: italic;
  color: var(--p-text-muted-color);
}
.done {
  text-decoration: line-through;
  color: var(--p-text-muted-color);
}
.actions {
  display: flex;
  gap: 0.25rem;
}
.rescheduled {
  margin-left: 0.35rem;
  font-size: 0.85rem;
  color: var(--p-amber-600);
}
.payment-form {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.balance-line {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
}
.packages {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}
.packages-label {
  font-size: 0.9rem;
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
  max-width: 28rem;
}
.hint {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
</style>
