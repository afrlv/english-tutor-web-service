import { describe, expect, it } from "vitest";

import { formatDateTime, formatMoney } from "./format";

describe("formatMoney", () => {
  it("форматирует строку из API", () => {
    // Intl использует неразрывные пробелы — сравниваем без них
    expect(formatMoney("1500.00").replace(/\s/g, "")).toBe("1500₽");
  });

  it("сохраняет копейки", () => {
    expect(formatMoney("99.50").replace(/\s/g, "")).toBe("99,5₽");
  });

  it("отдаёт прочерк для мусора", () => {
    expect(formatMoney("not-a-number")).toBe("—");
  });
});

describe("formatDateTime", () => {
  it("формат ДД.ММ.ГГГГ ЧЧ:ММ", () => {
    expect(formatDateTime("2026-06-11T14:00:00+03:00")).toMatch(
      /^\d{2}\.\d{2}\.\d{4},? \d{2}:\d{2}$/,
    );
  });
});
