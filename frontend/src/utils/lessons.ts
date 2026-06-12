import type { CancellationKind, LessonStatus } from "../api/types";

export const cancellationLabels: Record<CancellationKind, string> = {
  teacher: "отменил учитель",
  student: "предупредили заранее",
  late: "поздняя отмена / неявка",
};

export function statusLabel(status: LessonStatus): string {
  switch (status) {
    case "conducted":
      return "Проведён";
    case "cancelled":
      return "Отменён";
    default:
      return "Запланирован";
  }
}

export function statusSeverity(status: LessonStatus): string {
  switch (status) {
    case "conducted":
      return "success";
    case "cancelled":
      return "danger";
    default:
      return "info";
  }
}
