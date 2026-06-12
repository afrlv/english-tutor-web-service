import { describe, expect, it } from "vitest";

import { balanceInfo } from "./balance";

describe("balanceInfo", () => {
  it("положительный долг — задолженность", () => {
    const b = balanceInfo("3500.00", "1500.00");
    expect(b.kind).toBe("debt");
    expect(b.amount).toBe(3500);
    expect(b.renewalDue).toBe(false);
  });

  it("отрицательный долг — предоплата с пересчётом в уроки", () => {
    const b = balanceInfo("-12000.00", "1500.00");
    expect(b.kind).toBe("prepaid");
    expect(b.amount).toBe(12000);
    expect(b.lessonsLeft).toBe(8);
    expect(b.renewalDue).toBe(false);
  });

  it("неполный урок округляется вниз", () => {
    expect(balanceInfo("-4000", "1500").lessonsLeft).toBe(2);
  });

  it("осталось ≤ 2 уроков — пора продлевать", () => {
    expect(balanceInfo("-3000", "1500").renewalDue).toBe(true);
    expect(balanceInfo("-1000", "1500").renewalDue).toBe(true);
    expect(balanceInfo("-4500", "1500").renewalDue).toBe(false);
  });

  it("нулевая цена — сумма без пересчёта в уроки", () => {
    const b = balanceInfo("-5000", "0");
    expect(b.kind).toBe("prepaid");
    expect(b.lessonsLeft).toBeNull();
    expect(b.renewalDue).toBe(false);
  });

  it("нулевой баланс", () => {
    expect(balanceInfo("0", "1500").kind).toBe("zero");
  });
});
