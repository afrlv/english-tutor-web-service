<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Checkbox from "primevue/checkbox";
import Chip from "primevue/chip";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Textarea from "primevue/textarea";
import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  addHomework,
  addHomeworkLink,
  addLessonLink,
  cancelLesson,
  conductLesson,
  deleteAttachment,
  deleteHomework,
  deleteLesson,
  deleteLessonAttachment,
  getLessonDetail,
  type LessonInput,
  restoreLesson,
  revertLesson,
  updateHomework,
  updateLesson,
  uploadHomeworkFile,
  uploadLessonFile,
} from "../../api";
import type { CalendarLesson } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import AttachmentList from "../../components/AttachmentList.vue";
import CancelLessonDialog, { type CancelKind } from "../../components/CancelLessonDialog.vue";
import LessonDialog from "../../components/LessonDialog.vue";
import { formatDateTime, formatMoney } from "../../utils/format";
import { cancellationLabels, statusLabel, statusSeverity } from "../../utils/lessons";

const route = useRoute();
const router = useRouter();
const toast = useToast();
const confirm = useConfirm();
const lessonId = Number(route.params.id);

const lesson = ref<CalendarLesson | null>(null);
const editOpen = ref(false);
const cancelOpen = ref(false);
const acting = ref(false);

// материалы урока
const materialFileInput = ref<HTMLInputElement | null>(null);
const materialLinkUrl = ref("");
const materialLinkName = ref("");
// новое ДЗ
const hwText = ref("");
// вложения к конкретному ДЗ
const hwFileInput = ref<HTMLInputElement | null>(null);
const uploadHwId = ref<number | null>(null);
const hwLinkId = ref<number | null>(null);
const hwLinkUrl = ref("");
const hwLinkName = ref("");

const gradeOptions = [2, 3, 4, 5].map((g) => ({ label: String(g), value: g }));

function showError(e: unknown, fallback: string) {
  const detail =
    (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
  toast.add({ severity: "error", summary: "Ошибка", detail, life: 4000 });
}

async function load() {
  try {
    lesson.value = await getLessonDetail(lessonId);
  } catch {
    router.push("/students");
  }
}
load();

// --- статусные действия ---

async function onConduct() {
  acting.value = true;
  try {
    await conductLesson(lessonId);
    await load();
    toast.add({ severity: "success", summary: "Урок проведён, оплата начислена", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось отметить урок");
  } finally {
    acting.value = false;
  }
}

async function onRevert() {
  acting.value = true;
  try {
    await revertLesson(lessonId);
    await load();
  } catch (e) {
    showError(e, "Не удалось откатить урок");
  } finally {
    acting.value = false;
  }
}

async function onCancelConfirm(kind: CancelKind, comment: string | null, amount: string | null) {
  try {
    await cancelLesson(lessonId, kind, comment, amount);
    cancelOpen.value = false;
    await load();
  } catch (e) {
    showError(e, "Не удалось отменить урок");
  }
}

async function onRestore() {
  try {
    await restoreLesson(lessonId);
    await load();
  } catch (e) {
    showError(e, "Не удалось восстановить урок");
  }
}

function onDelete() {
  confirm.require({
    message: "Удалить урок целиком, вместе с материалами и ДЗ?",
    header: "Подтверждение",
    acceptLabel: "Удалить",
    rejectLabel: "Отмена",
    acceptProps: { severity: "danger" },
    accept: async () => {
      try {
        await deleteLesson(lessonId);
        router.push(`/students/${lesson.value?.student_id}`);
      } catch (e) {
        showError(e, "Не удалось удалить урок");
      }
    },
  });
}

async function saveEdit(data: LessonInput) {
  try {
    await updateLesson(lessonId, data);
    editOpen.value = false;
    await load();
  } catch (e) {
    showError(e, "Не удалось сохранить урок");
  }
}

// --- материалы урока ---

async function onMaterialFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  (event.target as HTMLInputElement).value = "";
  if (!file) return;
  try {
    await uploadLessonFile(lessonId, file);
    await load();
  } catch (e) {
    showError(e, "Не удалось загрузить файл");
  }
}

async function onAddMaterialLink() {
  if (!materialLinkUrl.value.trim()) return;
  try {
    await addLessonLink(lessonId, materialLinkUrl.value.trim(), materialLinkName.value.trim() || undefined);
    materialLinkUrl.value = "";
    materialLinkName.value = "";
    await load();
  } catch (e) {
    showError(e, "Не удалось добавить ссылку");
  }
}

async function onRemoveMaterial(id: number) {
  await deleteLessonAttachment(id);
  await load();
}

// --- домашнее задание ---

async function onAddHomework() {
  if (!hwText.value.trim()) return;
  try {
    await addHomework(lessonId, hwText.value.trim());
    hwText.value = "";
    await load();
  } catch (e) {
    showError(e, "Не удалось добавить задание");
  }
}

async function onGradeChange(hwId: number, grade: number | null) {
  if (grade === null) await updateHomework(hwId, { is_checked: false });
  else await updateHomework(hwId, { grade });
  await load();
}

async function onDeleteHomework(hwId: number) {
  await deleteHomework(hwId);
  await load();
}

function pickHwFile(hwId: number) {
  uploadHwId.value = hwId;
  hwFileInput.value?.click();
}

async function onHwFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  (event.target as HTMLInputElement).value = "";
  if (!file || uploadHwId.value === null) return;
  try {
    await uploadHomeworkFile(uploadHwId.value, file);
    await load();
  } catch (e) {
    showError(e, "Не удалось загрузить файл");
  }
}

async function onAddHwLink() {
  if (hwLinkId.value === null || !hwLinkUrl.value.trim()) return;
  try {
    await addHomeworkLink(hwLinkId.value, hwLinkUrl.value.trim(), hwLinkName.value.trim() || undefined);
    hwLinkId.value = null;
    hwLinkUrl.value = "";
    hwLinkName.value = "";
    await load();
  } catch (e) {
    showError(e, "Не удалось добавить ссылку");
  }
}

async function onRemoveHwAttachment(id: number) {
  await deleteAttachment(id);
  await load();
}
</script>

<template>
  <AppLayout>
    <template v-if="lesson">
      <Card class="head-card">
        <template #title>
          <div class="head">
            <Button
              icon="pi pi-arrow-left"
              text
              rounded
              @click="router.push(`/students/${lesson.student_id}`)"
            />
            <div class="head-main">
              <span>Урок: {{ lesson.student_name }}</span>
              <span class="when">
                {{ formatDateTime(lesson.scheduled_at) }} · {{ lesson.duration_minutes }} мин
                <template v-if="lesson.price !== null">
                  · {{ parseFloat(lesson.price) === 0 ? "бесплатный" : formatMoney(lesson.price) }}
                </template>
              </span>
            </div>
            <Tag :value="statusLabel(lesson.status)" :severity="statusSeverity(lesson.status)" />
          </div>
        </template>
        <template #content>
          <p v-if="lesson.cancellation_kind" class="muted">
            Причина: {{ cancellationLabels[lesson.cancellation_kind] }}
            <template v-if="lesson.cancellation_comment">— {{ lesson.cancellation_comment }}</template>
          </p>
          <p v-if="lesson.rescheduled_from" class="muted">
            Перенесён с {{ formatDateTime(lesson.rescheduled_from) }}
          </p>
          <div class="actions">
            <Button
              v-if="lesson.status === 'planned'"
              label="Проведён"
              icon="pi pi-check"
              severity="success"
              :loading="acting"
              @click="onConduct"
            />
            <Button
              v-if="lesson.status === 'conducted'"
              label="Откатить"
              icon="pi pi-undo"
              severity="warn"
              :loading="acting"
              @click="onRevert"
            />
            <Button
              v-if="lesson.status === 'planned'"
              label="Отменить"
              icon="pi pi-ban"
              severity="warn"
              outlined
              @click="cancelOpen = true"
            />
            <Button
              v-if="lesson.status === 'cancelled'"
              label="Восстановить"
              icon="pi pi-replay"
              severity="success"
              outlined
              @click="onRestore"
            />
            <Button label="Изменить" icon="pi pi-pencil" severity="secondary" @click="editOpen = true" />
            <a v-if="lesson.zoom_link" :href="lesson.zoom_link" target="_blank">
              <Button label="Zoom" icon="pi pi-video" severity="info" outlined />
            </a>
            <Button label="Удалить" icon="pi pi-trash" severity="danger" text @click="onDelete" />
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Тема и рекомендации</template>
        <template #content>
          <p><strong>Тема:</strong> {{ lesson.topic || "не указана" }}</p>
          <p class="pre"><strong>Рекомендации:</strong> {{ lesson.recommendation || "—" }}</p>
        </template>
      </Card>

      <Card>
        <template #title>Материалы урока</template>
        <template #content>
          <AttachmentList :attachments="lesson.attachments" removable @remove="onRemoveMaterial" />
          <p v-if="!lesson.attachments.length" class="muted">Материалов пока нет</p>
          <div class="material-add">
            <Button
              label="Файл"
              icon="pi pi-paperclip"
              severity="secondary"
              outlined
              size="small"
              @click="materialFileInput?.click()"
            />
            <InputText v-model="materialLinkUrl" placeholder="https://…" class="grow" size="small" />
            <InputText v-model="materialLinkName" placeholder="Подпись" class="name" size="small" />
            <Button
              icon="pi pi-plus"
              label="Ссылка"
              severity="secondary"
              outlined
              size="small"
              :disabled="!materialLinkUrl.trim()"
              @click="onAddMaterialLink"
            />
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Домашнее задание</template>
        <template #content>
          <div v-for="hw in lesson.homeworks" :key="hw.id" class="hw">
            <div class="hw-head">
              <Checkbox :model-value="hw.is_done" binary disabled />
              <span :class="{ done: hw.is_done }">{{ hw.description }}</span>
              <Select
                v-tooltip="'Оценка (выбор = проверено)'"
                :model-value="hw.grade"
                :options="gradeOptions"
                option-label="label"
                option-value="value"
                placeholder="Оценка"
                show-clear
                size="small"
                class="grade"
                @update:model-value="(v: number | null) => onGradeChange(hw.id, v)"
              />
              <Button
                v-tooltip="'Прикрепить файл'"
                icon="pi pi-paperclip"
                text
                rounded
                size="small"
                @click="pickHwFile(hw.id)"
              />
              <Button
                v-tooltip="'Добавить ссылку'"
                icon="pi pi-link"
                text
                rounded
                size="small"
                @click="hwLinkId = hw.id"
              />
              <Button
                icon="pi pi-trash"
                text
                rounded
                size="small"
                severity="danger"
                @click="onDeleteHomework(hw.id)"
              />
            </div>
            <AttachmentList :attachments="hw.attachments" removable @remove="onRemoveHwAttachment" />
            <p v-if="hw.student_answer" class="answer">Ответ ученика: {{ hw.student_answer }}</p>
          </div>
          <p v-if="!lesson.homeworks.length" class="muted">Заданий пока нет</p>

          <form class="hw-add" @submit.prevent="onAddHomework">
            <Textarea v-model="hwText" rows="2" placeholder="Новое задание" fluid />
            <Button type="submit" label="Добавить задание" icon="pi pi-plus" :disabled="!hwText.trim()" />
          </form>
        </template>
      </Card>
    </template>

    <LessonDialog v-model:visible="editOpen" :lesson="lesson" @save="saveEdit" />
    <CancelLessonDialog v-model:visible="cancelOpen" @confirm="onCancelConfirm" />

    <Dialog
      :visible="hwLinkId !== null"
      header="Ссылка к заданию"
      modal
      @update:visible="hwLinkId = null"
    >
      <form class="link-form" @submit.prevent="onAddHwLink">
        <InputText v-model="hwLinkUrl" placeholder="https://…" required fluid />
        <InputText v-model="hwLinkName" placeholder="Подпись (необязательно)" fluid />
        <Button type="submit" label="Добавить" :disabled="!hwLinkUrl.trim()" />
      </form>
    </Dialog>

    <input ref="materialFileInput" type="file" hidden @change="onMaterialFile" />
    <input ref="hwFileInput" type="file" hidden @change="onHwFile" />
  </AppLayout>
</template>

<style scoped>
.head-card {
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
.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.muted {
  color: var(--p-text-muted-color);
}
.pre {
  white-space: pre-wrap;
}
.material-add {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}
.grow {
  flex: 1;
  min-width: 12rem;
}
.name {
  width: 9rem;
}
.hw {
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--p-surface-200);
}
.hw-head {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.hw-head span {
  flex: 1;
}
.done {
  text-decoration: line-through;
  color: var(--p-text-muted-color);
}
.grade {
  width: 6.5rem;
}
.answer {
  margin: 0.3rem 0 0;
  font-style: italic;
  color: var(--p-text-muted-color);
}
.hw-add {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
  margin-top: 1rem;
}
.link-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 22rem;
}
:deep(.p-card) {
  margin-bottom: 1rem;
}
</style>
