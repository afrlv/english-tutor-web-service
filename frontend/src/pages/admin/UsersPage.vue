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
import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";

import { computed } from "vue";

import {
  adminCreateUser,
  adminDeleteUser,
  adminListDeletedUsers,
  adminListUsers,
  adminRestoreUser,
  adminSetPassword,
  adminUpdateUser,
  assignTeacher,
  listUnassignedStudents,
} from "../../api";
import type { User } from "../../api/types";
import { useAuthStore } from "../../stores/auth";
import AppLayout from "../../components/AppLayout.vue";

const toast = useToast();
const confirm = useConfirm();
const auth = useAuthStore();

const users = ref<User[]>([]);
const deletedUsers = ref<User[]>([]);
const showDeleted = ref(false);
const loading = ref(true);
const createOpen = ref(false);
const passwordUser = ref<User | null>(null);
const newPassword = ref("");
const saving = ref(false);
const editUser = ref<User | null>(null);
const editForm = ref({ full_name: "", login: "", email: "" });

// Привязка непривязанных учеников к учителю
const unassignedIds = ref<Set<number>>(new Set());
const assignUser = ref<User | null>(null);
const assignTeacherId = ref<number | null>(null);
const teachers = computed(() =>
  users.value
    .filter((u) => u.role === "teacher" && u.is_active)
    .map((u) => ({ label: `${u.full_name} (${u.email})`, value: u.id })),
);

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
    const [list, unassigned] = await Promise.all([
      adminListUsers(),
      listUnassignedStudents(),
    ]);
    users.value = list;
    unassignedIds.value = new Set(unassigned.map((u) => u.user_id));
    if (showDeleted.value) deletedUsers.value = await adminListDeletedUsers();
  } finally {
    loading.value = false;
  }
}

async function doAssignTeacher() {
  if (!assignUser.value || assignTeacherId.value === null) return;
  saving.value = true;
  try {
    await assignTeacher(assignUser.value.id, assignTeacherId.value);
    toast.add({ severity: "success", summary: "Ученик привязан к учителю", life: 3000 });
    assignUser.value = null;
    assignTeacherId.value = null;
    await load();
  } catch (e) {
    showError(e, "Не удалось привязать ученика");
  } finally {
    saving.value = false;
  }
}

async function toggleDeleted() {
  showDeleted.value = !showDeleted.value;
  if (showDeleted.value) deletedUsers.value = await adminListDeletedUsers();
}

async function onRestoreUser(user: User) {
  try {
    await adminRestoreUser(user.id);
    toast.add({ severity: "success", summary: "Учётная запись восстановлена", life: 3000 });
    await Promise.all([
      (async () => (users.value = await adminListUsers()))(),
      (async () => (deletedUsers.value = await adminListDeletedUsers()))(),
    ]);
  } catch (e) {
    showError(e, "Не удалось восстановить учётную запись");
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

function onDeleteUser(user: User) {
  confirm.require({
    message: `Удалить учётную запись «${user.full_name}» (${user.email})? Вход будет закрыт, учётка скроется. Данные в базе сохранятся.`,
    header: "Удаление учётной записи",
    acceptLabel: "Удалить",
    rejectLabel: "Отмена",
    acceptProps: { severity: "danger" },
    accept: async () => {
      try {
        await adminDeleteUser(user.id);
        toast.add({ severity: "success", summary: "Учётная запись удалена", life: 3000 });
        await load();
      } catch (e) {
        showError(e, "Не удалось удалить учётную запись");
      }
    },
  });
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

</script>

<template>
  <AppLayout>
    <Card>
      <template #title>
        <div class="header">
          Пользователи
          <div class="header-actions">
            <Button
              :label="showDeleted ? 'Скрыть удалённые' : 'Удалённые'"
              :icon="showDeleted ? 'pi pi-eye-slash' : 'pi pi-trash'"
              severity="secondary"
              text
              @click="toggleDeleted"
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
                v-if="data.role === 'student' && unassignedIds.has(data.id)"
                v-tooltip="'Ученик не привязан к учителю'"
                label="Назначить учителя"
                icon="pi pi-link"
                severity="warn"
                text
                size="small"
                @click="assignUser = data"
              />
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
              <Button
                v-if="data.id !== auth.user?.id"
                v-tooltip="'Удалить учётную запись'"
                icon="pi pi-trash"
                text
                rounded
                size="small"
                severity="danger"
                @click="onDeleteUser(data)"
              />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <Card v-if="showDeleted" class="deleted-card">
      <template #title>Удалённые учётные записи</template>
      <template #content>
        <DataTable :value="deletedUsers" data-key="id">
          <template #empty>Удалённых учётных записей нет</template>
          <Column field="id" header="ID" />
          <Column field="full_name" header="Имя" />
          <Column field="login" header="Логин" />
          <Column field="email" header="Почта" />
          <Column header="Роль">
            <template #body="{ data }">{{ roleLabel(data.role) }}</template>
          </Column>
          <Column header="">
            <template #body="{ data }">
              <Button
                label="Восстановить"
                icon="pi pi-replay"
                severity="success"
                text
                size="small"
                @click="onRestoreUser(data)"
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
      :visible="assignUser !== null"
      :header="`Привязать к учителю: ${assignUser?.full_name ?? ''}`"
      modal
      @update:visible="assignUser = null"
    >
      <form class="form" @submit.prevent="doAssignTeacher">
        <label>
          Учитель
          <Select
            v-model="assignTeacherId"
            :options="teachers"
            option-label="label"
            option-value="value"
            placeholder="Выберите учителя"
            fluid
          />
        </label>
        <Button
          type="submit"
          label="Привязать"
          :loading="saving"
          :disabled="assignTeacherId === null"
        />
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
.deleted-card {
  margin-top: 1rem;
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
