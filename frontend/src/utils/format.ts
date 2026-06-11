const moneyFormat = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});

/** "1500.00" → "1 500 ₽" */
export function formatMoney(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(num)) return "—";
  return moneyFormat.format(num);
}

/** ISO-строка → "11.06.2026 14:00" */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** ISO-строка → "11.06.2026" */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU");
}
