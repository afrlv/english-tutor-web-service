/** Озвучка текста средствами браузера (бесплатно, без бэкенда). */
export function speak(text: string, lang = "en-US"): void {
  const synth = window.speechSynthesis;
  if (!synth || !text.trim()) return;
  synth.cancel(); // прервать предыдущую фразу
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = lang;
  synth.speak(utter);
}

/** Доступна ли озвучка в этом браузере. */
export function canSpeak(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}
