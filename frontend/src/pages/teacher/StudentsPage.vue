<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { createStudent, listStudents } from "../../api";
import type { Student } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { formatDate } from "../../utils/format";

const router = useRouter();
const toast = useToast();

const students = ref<Student[]>([]);
const loading = ref(true);
const dialogOpen = ref(false);
const saving = ref(false);
const form = ref({ email: "", full_name: "" });

async function load() {
  loading.value = true;
  try {
    students.value = await listStudents();
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    await createStudent(form.value);
    dialogOpen.value = false;
    form.value = { email: "", full_name: "" };
    toast.add({
      severity: "success",
      summary: "Ученик создан",
      detail: "Логин и пароль отправлены на почту",
      life: 4000,
    });
    await load();
  } catch (e: unknown) {
    const detail =
      (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
      "Не удалось создать ученика";
    toast.add({ severity: "error", summary: "Ошибка", detail, life: 4000 });
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <AppLayout>
    <Card>
      <template #title>
        <div class="header">
          Ученики
          <Button label="Добавить ученика" icon="pi pi-plus" @click="dialogOpen = true" />
        </div>
      </template>
      <template #content>
        <DataTable
          :value="students"
          :loading="loading"
          selection-mode="single"
          @row-select="(e) => router.push(`/students/${e.data.id}`)"
        >
          <template #empty>Пока нет учеников</template>
          <Column field="user.full_name" header="Имя" />
          <Column field="user.email" header="Почта" />
          <Column header="Добавлен">
            <template #body="{ data }">{{ formatDate(data.created_at) }}</template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <Dialog v-model:visible="dialogOpen" header="Новый ученик" modal class="dialog">
      <form class="form" @submit.prevent="save">
        <label>
          Имя и фамилия
          <InputText v-model="form.full_name" required fluid />
        </label>
        <label>
          Почта (туда придут логин и пароль)
          <InputText v-model="form.email" type="email" required fluid />
        </label>
        <Button type="submit" label="Создать" :loading="saving" />
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
