<script setup lang="ts">
import Button from "primevue/button";
import Select from "primevue/select";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { impersonate, impersonationTargets, stopImpersonation } from "../api";
import type { Role, User } from "../api/types";
import { useAuthStore } from "../stores/auth";
import { roleHome } from "../utils/access";

const auth = useAuthStore();
const router = useRouter();
const toast = useToast();

const targets = ref<User[]>([]);
const switching = ref(false);

const SELF = -1;

const roleLabels: Record<Role, string> = {
  superuser: "суперпользователь",
  teacher: "учитель",
  student: "ученик",
  parent: "родитель",
};

const options = computed(() => [
  { label: "Суперпользователь (мой профиль)", value: SELF },
  ...targets.value.map((t) => ({
    label: `${t.full_name} — ${roleLabels[t.role]}`,
    value: t.id,
  })),
]);

const current = computed(() => (auth.user?.impersonating ? auth.user.id : SELF));

onMounted(async () => {
  try {
    targets.value = await impersonationTargets();
  } catch {
    // список не критичен — строка останется без вариантов
  }
});

async function applyUser(user: User) {
  auth.user = user;
  await router.push(roleHome(user.role));
}

async function switchTo(value: number) {
  if (value === current.value || switching.value) return;
  switching.value = true;
  try {
    if (auth.user?.impersonating) {
      // сначала возвращаемся в суперюзера — только он может начать новый просмотр
      await stopImpersonation();
    }
    const user = value === SELF ? await stopImpersonation().catch(() => null) : await impersonate(value);
    if (user) await applyUser(user);
    else {
      // value === SELF и мы уже были собой
      auth.user = { ...auth.user!, impersonating: false };
    }
  } catch {
    toast.add({
      severity: "error",
      summary: "Не удалось переключить профиль",
      life: 4000,
    });
  } finally {
    switching.value = false;
  }
}

async function back() {
  await switchTo(SELF);
}
</script>

<template>
  <div class="bar" :class="{ viewing: auth.user?.impersonating }">
    <i class="pi pi-shield" />
    <span v-if="auth.user?.impersonating">
      Вы суперпользователь — просмотр от имени:
      <strong>{{ auth.user.full_name }} ({{ roleLabels[auth.user.role] }})</strong>
    </span>
    <span v-else>Вы вошли как суперпользователь</span>
    <Select
      :model-value="current"
      :options="options"
      option-label="label"
      option-value="value"
      size="small"
      :loading="switching"
      placeholder="Выбрать профиль"
      class="select"
      @update:model-value="switchTo"
    />
    <Button
      v-if="auth.user?.impersonating"
      label="Вернуться в свой профиль"
      icon="pi pi-sign-in"
      size="small"
      severity="contrast"
      text
      @click="back"
    />
  </div>
</template>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 1rem;
  background: var(--p-blue-50);
  border-bottom: 1px solid var(--p-blue-200);
  color: var(--p-blue-900);
  font-size: 0.9rem;
}
.bar.viewing {
  background: var(--p-amber-100);
  border-bottom-color: var(--p-amber-300);
  color: var(--p-amber-900);
}
.select {
  min-width: 18rem;
}
</style>
