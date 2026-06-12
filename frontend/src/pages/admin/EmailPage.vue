<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Password from "primevue/password";
import SelectButton from "primevue/selectbutton";
import Tag from "primevue/tag";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";

import {
  adminSendDigest,
  getEmailSettings,
  listEmailLog,
  saveEmailSettings,
  sendTestEmail,
} from "../../api";
import type { EmailLogEntry } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { formatDateTime } from "../../utils/format";

const toast = useToast();

const backend = ref<"console" | "smtp">("console");
const form = ref({ smtp_host: "", smtp_port: 587, smtp_user: "", smtp_from: "" });
const newPassword = ref("");
const passwordSet = ref(false);
const saving = ref(false);
const testing = ref(false);

const log = ref<EmailLogEntry[]>([]);
const logLoading = ref(true);

const backendOptions = [
  { label: "В лог (без отправки)", value: "console" },
  { label: "SMTP (реальная отправка)", value: "smtp" },
];

function showError(e: unknown, fallback: string) {
  const detail =
    (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
  toast.add({ severity: "error", summary: "Ошибка", detail, life: 4000 });
}

async function loadSettings() {
  const s = await getEmailSettings();
  backend.value = s.backend;
  form.value = {
    smtp_host: s.smtp_host,
    smtp_port: s.smtp_port,
    smtp_user: s.smtp_user,
    smtp_from: s.smtp_from,
  };
  passwordSet.value = s.password_set;
}

async function loadLog() {
  logLoading.value = true;
  try {
    log.value = await listEmailLog();
  } finally {
    logLoading.value = false;
  }
}

onMounted(() => {
  loadSettings();
  loadLog();
});

async function save() {
  saving.value = true;
  try {
    const s = await saveEmailSettings({
      backend: backend.value,
      ...form.value,
      smtp_password: newPassword.value || null,
    });
    passwordSet.value = s.password_set;
    newPassword.value = "";
    toast.add({ severity: "success", summary: "Настройки сохранены", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось сохранить настройки");
  } finally {
    saving.value = false;
  }
}

async function test() {
  testing.value = true;
  try {
    const { ok } = await sendTestEmail();
    if (ok) {
      toast.add({
        severity: "success",
        summary: "Тестовое письмо отправлено",
        detail: "Проверьте почту администратора и журнал",
        life: 4000,
      });
    } else {
      toast.add({
        severity: "error",
        summary: "Отправка не удалась",
        detail: "Подробности в журнале ниже",
        life: 5000,
      });
    }
    await loadLog();
  } catch (e) {
    showError(e, "Не удалось отправить тестовое письмо");
  } finally {
    testing.value = false;
  }
}

async function sendDigest() {
  try {
    await adminSendDigest();
    toast.add({ severity: "success", summary: "Дайджест отправлен учителю", life: 3000 });
    await loadLog();
  } catch (e) {
    showError(e, "Не удалось отправить дайджест");
  }
}
</script>

<template>
  <AppLayout>
    <div class="grid">
      <Card>
        <template #title>Настройки отправки почты</template>
        <template #content>
          <form class="form" @submit.prevent="save">
            <SelectButton
              v-model="backend"
              :options="backendOptions"
              option-label="label"
              option-value="value"
              :allow-empty="false"
            />
            <template v-if="backend === 'smtp'">
              <div class="row2">
                <label>
                  SMTP-сервер
                  <InputText v-model="form.smtp_host" placeholder="smtp.yandex.ru" fluid />
                </label>
                <label>
                  Порт
                  <InputNumber v-model="form.smtp_port" :use-grouping="false" fluid />
                </label>
              </div>
              <label>
                Логин (почтовый ящик)
                <InputText v-model="form.smtp_user" placeholder="tutor@yandex.ru" fluid />
              </label>
              <label>
                Пароль {{ passwordSet ? "(оставьте пустым, чтобы не менять)" : "(пароль приложения)" }}
                <Password
                  v-model="newPassword"
                  :feedback="false"
                  toggle-mask
                  :placeholder="passwordSet ? '••••••••' : ''"
                  fluid
                />
              </label>
              <label>
                Адрес отправителя (если отличается от логина)
                <InputText v-model="form.smtp_from" fluid />
              </label>
              <p class="hint">
                Gmail: smtp.gmail.com, порт 587, пароль приложения.
                Яндекс: smtp.yandex.ru, порт 465, пароль приложения.
              </p>
            </template>
            <p v-else class="hint">
              Письма не отправляются, а пишутся в журнал и лог сервера — режим для проверки.
            </p>
            <div class="actions">
              <Button type="submit" label="Сохранить" :loading="saving" />
              <Button
                label="Тестовое письмо"
                icon="pi pi-send"
                severity="secondary"
                :loading="testing"
                @click="test"
              />
              <Button
                label="Дайджест учителю сейчас"
                icon="pi pi-envelope"
                severity="secondary"
                text
                @click="sendDigest"
              />
            </div>
          </form>
        </template>
      </Card>

      <Card>
        <template #title>
          <div class="log-header">
            Журнал отправки
            <Button icon="pi pi-refresh" text rounded size="small" @click="loadLog" />
          </div>
        </template>
        <template #content>
          <DataTable :value="log" :loading="logLoading" paginator :rows="20">
            <template #empty>Писем ещё не отправлялось</template>
            <Column header="Когда">
              <template #body="{ data }">{{ formatDateTime(data.created_at) }}</template>
            </Column>
            <Column field="to_email" header="Кому" />
            <Column field="subject" header="Тема" />
            <Column header="Статус">
              <template #body="{ data }">
                <Tag
                  :value="data.status === 'sent' ? 'Отправлено' : 'Ошибка'"
                  :severity="data.status === 'sent' ? 'success' : 'danger'"
                />
              </template>
            </Column>
            <Column header="Ошибка">
              <template #body="{ data }">
                <span class="error-text">{{ data.error ?? "" }}</span>
              </template>
            </Column>
          </DataTable>
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
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 32rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}
.row2 {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1rem;
}
.hint {
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
  margin: 0;
}
.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.error-text {
  font-size: 0.85rem;
  color: var(--p-red-600);
}
</style>
