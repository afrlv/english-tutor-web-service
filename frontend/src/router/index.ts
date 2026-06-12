import { createRouter, createWebHistory } from "vue-router";

import { onUnauthorized } from "../api/client";
import type { Role } from "../api/types";
import { useAuthStore } from "../stores/auth";
import { canAccess, roleHome } from "../utils/access";

declare module "vue-router" {
  interface RouteMeta {
    roles?: Role[];
  }
}

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("../pages/LoginPage.vue") },
    {
      path: "/dashboard",
      component: () => import("../pages/teacher/DashboardPage.vue"),
      meta: { roles: ["teacher"] },
    },
    {
      path: "/students",
      component: () => import("../pages/teacher/StudentsPage.vue"),
      meta: { roles: ["teacher", "superuser"] },
    },
    {
      path: "/students/:id",
      component: () => import("../pages/teacher/StudentCardPage.vue"),
      meta: { roles: ["teacher", "superuser"] },
    },
    // Финансы переехали на главную учителя
    { path: "/finance", redirect: "/dashboard" },
    {
      path: "/cabinet",
      component: () => import("../pages/student/CabinetPage.vue"),
      meta: { roles: ["student"] },
    },
    {
      path: "/study/:id",
      component: () => import("../pages/student/StudyPage.vue"),
      meta: { roles: ["student"] },
    },
    {
      path: "/child",
      component: () => import("../pages/parent/ChildPage.vue"),
      meta: { roles: ["parent"] },
    },
    {
      path: "/balance",
      component: () => import("../pages/parent/BalancePage.vue"),
      meta: { roles: ["parent"] },
    },
    {
      path: "/admin/users",
      component: () => import("../pages/admin/UsersPage.vue"),
      meta: { roles: ["superuser"] },
    },
    {
      path: "/admin/email",
      component: () => import("../pages/admin/EmailPage.vue"),
      meta: { roles: ["superuser"] },
    },
    { path: "/", redirect: "/login" },
    { path: "/:pathMatch(.*)*", redirect: "/login" },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  await auth.ensureLoaded();

  if (to.path === "/login") {
    return auth.user ? roleHome(auth.user.role) : true;
  }
  if (!auth.user) return "/login";
  if (!canAccess(auth.user.role, to.meta.roles)) return roleHome(auth.user.role);
  return true;
});

onUnauthorized(() => {
  const auth = useAuthStore();
  auth.reset();
  if (router.currentRoute.value.path !== "/login") router.push("/login");
});
