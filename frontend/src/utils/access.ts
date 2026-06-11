import type { Role } from "../api/types";

/** Домашняя страница каждой роли — редирект после логина и при отказе в доступе. */
export function roleHome(role: Role): string {
  switch (role) {
    case "superuser":
      return "/admin/users";
    case "teacher":
      return "/dashboard";
    case "student":
      return "/cabinet";
    case "parent":
      return "/child";
  }
}

export function canAccess(role: Role, allowed?: Role[]): boolean {
  if (!allowed || allowed.length === 0) return true;
  return allowed.includes(role);
}
