/** Расстояние Левенштейна между строками (число вставок/удалений/замен). */
export function levenshtein(a: string, b: string): number {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;

  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  let curr = new Array<number>(b.length + 1);
  for (let i = 1; i <= a.length; i++) {
    curr[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost);
    }
    [prev, curr] = [curr, prev];
  }
  return prev[b.length];
}

/**
 * «Почти верно»: одна опечатка на достаточно длинном слове прощается.
 * Точное совпадение тоже true. Строки должны быть уже нормализованы.
 */
export function isCloseEnough(answer: string, expected: string): boolean {
  if (answer === expected) return true;
  if (expected.length < 4) return false; // на коротких словах опечатка = другое слово
  return levenshtein(answer, expected) <= 1;
}
