<script setup lang="ts">
import Avatar from "primevue/avatar";
import Button from "primevue/button";
import Menubar from "primevue/menubar";
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";
import ImpersonationBar from "./ImpersonationBar.vue";

const auth = useAuthStore();
const router = useRouter();

// Строка видна и в своём профиле суперюзера, и в режиме просмотра от чужого имени
const showImpersonationBar = computed(
  () => auth.user?.role === "superuser" || auth.user?.impersonating,
);

const items = computed(() => {
  const role = auth.user?.role;
  // Суперюзер настраивает систему: расписание и финансы — зона учителя
  if (role === "superuser") {
    return [
      { label: "Пользователи", icon: "pi pi-cog", command: () => router.push("/admin/users") },
      { label: "Ученики", icon: "pi pi-users", command: () => router.push("/students") },
      { label: "Почта", icon: "pi pi-envelope", command: () => router.push("/admin/email") },
    ];
  }
  if (role === "teacher") {
    return [
      { label: "Главная", icon: "pi pi-calendar", command: () => router.push("/dashboard") },
      { label: "Ученики", icon: "pi pi-users", command: () => router.push("/students") },
    ];
  }
  if (role === "student") {
    return [{ label: "Мой кабинет", icon: "pi pi-home", command: () => router.push("/cabinet") }];
  }
  if (role === "parent") {
    return [
      { label: "Ребёнок", icon: "pi pi-user", command: () => router.push("/child") },
      { label: "Оплата", icon: "pi pi-wallet", command: () => router.push("/balance") },
    ];
  }
  return [];
});

async function onLogout() {
  await auth.logout();
  router.push("/login");
}
</script>

<template>
  <ImpersonationBar v-if="showImpersonationBar" />
  <Menubar :model="items">
    <template #end>
      <div class="user-box">
        <Avatar
          v-if="auth.user?.avatar_path"
          :image="`/api/files/${auth.user.avatar_path}`"
          shape="circle"
        />
        <span>{{ auth.user?.full_name }}</span>
        <Button
          label="Выйти"
          icon="pi pi-sign-out"
          severity="secondary"
          text
          size="small"
          @click="onLogout"
        />
      </div>
    </template>
  </Menubar>
  <main class="page">
    <slot />
  </main>
</template>

<style scoped>
.page {
  max-width: 1100px;
  margin: 1.5rem auto;
  padding: 0 1rem;
}
.user-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
