<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Tag from "primevue/tag";
import ToggleSwitch from "primevue/toggleswitch";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";

import {
  adminCreateUser,
  adminListUsers,
  adminSendDigest,
  adminSetPassword,
  adminUpdateUser,
} from "../../api";
import type { User } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";

const toast = useToast();

const users = ref<User[]>([]);
const loading = ref(true);
const createOpen = ref(false);
const passwordUser = ref<User | null>(null);
const newPassword = ref("");
const saving = ref(false);
const editUser = ref<User | null>(null);
const editForm = ref({ full_name: "", login: "", email: "" });

const roleOptions = [
  { label: "Суперюзер", value: "superuser" },
  { label: "Учитель", value: "teacher" },
  { label: "Ученик", value: "student" },
  { label: "Родитель", value: "parent" },
];

const roleLabel = (role: string) =>
  roleOptions.find((r) => r.value === role)?.label ?? role;

const form = ref({ email: "", login: "", full_name: "", role: "student", password: "" });

function showError(e: unknown, fallback: string) {
  const detail =
    (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
  toast.add({ severity: "error", summary: "Ошибка", detail, life: 4000 });
}

async function load() {
  loading.value = true;
  try {
    users.value = await adminListUsers();
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function createUser() {
  saving.value = true;
  try {
    await adminCreateUser({ ...form.value, login: form.value.login || undefined });
    createOpen.value = false;
    form.value = { email: "", login: "", full_name: "", role: "student", password: "" };
    toast.add({ severity: "success", summary: "Пользователь создан", life: 3000 });
    await load();
  } catch (e) {
    showError(e, "Не удалось создать пользователя");
  } finally {
    saving.value = false;
  }
}

function openEdit(user: User) {
  editUser.value = user;
  editForm.value = { full_name: user.full_name, login: user.login, email: user.email };
}

async function saveEdit() {
  if (!editUser.value) return;
  saving.value = true;
  try {
    await adminUpdateUser(editUser.value.id, editForm.value);
    editUser.value = null;
    toast.add({ severity: "success", summary: "Пользователь обновлён", life: 3000 });
    await load();
  } catch (e) {
    showError(e, "Не удалось сохранить изменения");
  } finally {
    saving.value = false;
  }
}

async function toggleActive(user: User, is_active: boolean) {
  try {
    await adminUpdateUser(user.id, { is_active });
    await load();
  } catch (e) {
    showError(e, "Не удалось изменить статус");
  }
}

async function changeRole(user: User, role: string) {
  try {
    await adminUpdateUser(user.id, { role: role as User["role"] });
    await load();
  } catch (e) {
    showError(e, "Не удалось изменить роль");
  }
}

async function setPassword() {
  if (!passwordUser.value || !newPassword.value) return;
  try {
    await adminSetPassword(passwordUser.value.id, newPassword.value);
    toast.add({ severity: "success", summary: "Пароль установлен", life: 3000 });
    passwordUser.value = null;
    newPassword.value = "";
  } catch (e) {
    showError(e, "Не удалось установить пароль");
  }
}

async function sendDigest() {
  try {
    await adminSendDigest();
    toast.add({ severity: "success", summary: "Дайджест отправлен", life: 3000 });
  } catch (e) {
    showError(e, "Не удалось отправить дайджест");
  }
}
</script>

<template>
  <AppLayout>
    <Card>
      <template #title>
        <div class="header">
          Пользователи
          <div class="header-actions">
            <Button
              label="Дайджест сейчас"
              icon="pi pi-envelope"
              severity="secondary"
              @click="sendDigest"
            />
            <Button label="Создать" icon="pi pi-plus" @click="createOpen = true" />
          </div>
        </div>
      </template>
      <template #content>
        <DataTable :value="users" :loading="loading" data-key="id">
          <Column field="id" header="ID" />
          <Column field="full_name" header="Имя" />
          <Column field="login" header="Логин" />
          <Column field="email" header="Почта" />
          <Column header="Роль">
            <template #body="{ data }">
              <Select
                :model-value="data.role"
                :options="roleOptions"
                option-label="label"
                option-value="value"
                size="small"
                @update:model-value="(v: string) => changeRole(data, v)"
              />
            </template>
          </Column>
          <Column header="Активен">
            <template #body="{ data }">
              <ToggleSwitch
                :model-value="data.is_active"
                @update:model-value="(v: boolean) => toggleActive(data, v)"
              />
            </template>
          </Column>
          <Column header="">
            <template #body="{ data }">
              <Button
                v-tooltip="'Изменить имя, логин, почту'"
                icon="pi pi-pencil"
                text
                size="small"
                @click="openEdit(data)"
              />
              <Button
                label="Пароль"
                icon="pi pi-key"
                text
                size="small"
                @click="passwordUser = data"
              />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <Dialog v-model:visible="createOpen" header="Новый пользователь" modal>
      <form class="form" @submit.prevent="createUser">
        <label>
          Имя и фамилия
          <InputText v-model="form.full_name" required fluid />
        </label>
        <label>
          Почта
          <InputText v-model="form.email" type="email" required fluid />
        </label>
        <label>
          Логин (если пусто — почта)
          <InputText v-model="form.login" fluid />
        </label>
        <label>
          Роль
          <Select
            v-model="form.role"
            :options="roleOptions"
            option-label="label"
            option-value="value"
            fluid
          />
        </label>
        <label>
          Пароль
          <InputText v-model="form.password" required fluid />
        </label>
        <Button type="submit" label="Создать" :loading="saving" />
      </form>
    </Dialog>

    <Dialog
      :visible="editUser !== null"
      :header="`Редактирование: ${editUser?.full_name ?? ''}`"
      modal
      @update:visible="editUser = null"
    >
      <form class="form" @submit.prevent="saveEdit">
        <label>
          Имя и фамилия
          <InputText v-model="editForm.full_name" required fluid />
        </label>
        <label>
          Логин
          <InputText v-model="editForm.login" required fluid />
        </label>
        <label>
          Почта
          <InputText v-model="editForm.email" type="email" required fluid />
        </label>
        <Button type="submit" label="Сохранить" :loading="saving" />
      </form>
    </Dialog>

    <Dialog
      :visible="passwordUser !== null"
      :header="`Пароль: ${passwordUser?.full_name ?? ''}`"
      modal
      @update:visible="passwordUser = null"
    >
      <form class="form" @submit.prevent="setPassword">
        <label>
          Новый пароль
          <InputText v-model="newPassword" required fluid />
        </label>
        <Button type="submit" label="Установить" severity="warn" />
      </form>
    </Dialog>
  </AppLayout>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-actions {
  display: flex;
  gap: 0.5rem;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 20rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}
</style>
