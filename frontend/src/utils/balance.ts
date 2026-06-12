export interface BalanceInfo {
  kind: "debt" | "prepaid" | "zero";
  /** Положительная сумма долга или предоплаты */
  amount: number;
  /** Сколько целых уроков покрывает предоплата (null, если цена неизвестна) */
  lessonsLeft: number | null;
  /** Предоплата заканчивается (осталось ≤ 2 уроков) — пора продлевать */
  renewalDue: boolean;
}

/** Превращает «долг» из леджера в понятный человеку баланс.
 *  debt > 0 — задолженность; debt < 0 — предоплата (абонемент). */
export function balanceInfo(debt: string | number, lessonPrice: string | number): BalanceInfo {
  const d = typeof debt === "string" ? parseFloat(debt) : debt;
  const price = typeof lessonPrice === "string" ? parseFloat(lessonPrice) : lessonPrice;

  if (!Number.isFinite(d) || d === 0) {
    return { kind: "zero", amount: 0, lessonsLeft: null, renewalDue: false };
  }
  if (d > 0) {
    return { kind: "debt", amount: d, lessonsLeft: null, renewalDue: false };
  }
  const prepaid = -d;
  const lessonsLeft = price > 0 ? Math.floor(prepaid / price) : null;
  return {
    kind: "prepaid",
    amount: prepaid,
    lessonsLeft,
    renewalDue: lessonsLeft !== null && lessonsLeft <= 2,
  };
}
