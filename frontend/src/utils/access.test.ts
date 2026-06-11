import { describe, expect, it } from "vitest";

import type { Role } from "../api/types";
import { canAccess, roleHome } from "./access";

describe("roleHome", () => {
  it.each<[Role, string]>([
    ["superuser", "/admin/users"],
    ["teacher", "/dashboard"],
    ["student", "/cabinet"],
    ["parent", "/child"],
  ])("у роли %s домашняя страница %s", (role, home) => {
    expect(roleHome(role)).toBe(home);
  });
});

describe("canAccess", () => {
  it("маршрут без ограничений доступен всем", () => {
    expect(canAccess("student", undefined)).toBe(true);
    expect(canAccess("parent", [])).toBe(true);
  });

  it("роль из списка проходит", () => {
    expect(canAccess("teacher", ["teacher", "superuser"])).toBe(true);
    expect(canAccess("superuser", ["teacher", "superuser"])).toBe(true);
  });

  it("чужая роль не проходит", () => {
    expect(canAccess("student", ["teacher", "superuser"])).toBe(false);
    expect(canAccess("parent", ["student"])).toBe(false);
  });
});
