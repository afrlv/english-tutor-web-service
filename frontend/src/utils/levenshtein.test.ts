import { describe, expect, it } from "vitest";

import { isCloseEnough, levenshtein } from "./levenshtein";

describe("levenshtein", () => {
  it("совпадение — 0", () => {
    expect(levenshtein("cat", "cat")).toBe(0);
  });
  it("одна замена/вставка/удаление — 1", () => {
    expect(levenshtein("cat", "cot")).toBe(1);
    expect(levenshtein("the", "teh")).toBe(2); // транспозиция = 2 правки
    expect(levenshtein("color", "colour")).toBe(1);
  });
  it("пустые строки", () => {
    expect(levenshtein("", "abc")).toBe(3);
    expect(levenshtein("abc", "")).toBe(3);
  });
});

describe("isCloseEnough", () => {
  it("точное совпадение", () => {
    expect(isCloseEnough("apple", "apple")).toBe(true);
  });
  it("одна опечатка на длинном слове прощается", () => {
    expect(isCloseEnough("appl", "apple")).toBe(true);
    expect(isCloseEnough("aple", "apple")).toBe(true);
  });
  it("две опечатки не прощаются", () => {
    expect(isCloseEnough("aplpe", "apple")).toBe(false); // 2 замены
  });
  it("на коротком слове опечатка = другое слово", () => {
    expect(isCloseEnough("cot", "cat")).toBe(false);
  });
});
