import { defineStore } from "pinia";
import { ref } from "vue";

import * as apiAuth from "../api";
import type { User } from "../api/types";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const loaded = ref(false);

  async function ensureLoaded() {
    if (loaded.value) return;
    try {
      user.value = await apiAuth.fetchMe();
    } catch {
      user.value = null;
    } finally {
      loaded.value = true;
    }
  }

  async function login(email: string, password: string) {
    user.value = await apiAuth.login(email, password);
    loaded.value = true;
  }

  async function logout() {
    try {
      await apiAuth.logout();
    } finally {
      user.value = null;
    }
  }

  function reset() {
    user.value = null;
    loaded.value = true;
  }

  return { user, loaded, ensureLoaded, login, logout, reset };
});
