<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Password from "primevue/password";
import { useToast } from "primevue/usetoast";
import { ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";
import { roleHome } from "../utils/access";

const auth = useAuthStore();
const router = useRouter();
const toast = useToast();

const email = ref("");
const password = ref("");
const loading = ref(false);

async function submit() {
  loading.value = true;
  try {
    await auth.login(email.value, password.value);
    router.push(roleHome(auth.user!.role));
  } catch {
    toast.add({
      severity: "error",
      summary: "Не удалось войти",
      detail: "Проверьте почту и пароль",
      life: 4000,
    });
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-wrap">
    <Card class="login-card">
      <template #title>Кабинет репетитора</template>
      <template #content>
        <form class="login-form" @submit.prevent="submit">
          <InputText v-model="email" placeholder="Логин или почта" required autofocus />
          <Password
            v-model="password"
            placeholder="Пароль"
            :feedback="false"
            toggle-mask
            required
            fluid
          />
          <Button type="submit" label="Войти" :loading="loading" />
        </form>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  width: 22rem;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
