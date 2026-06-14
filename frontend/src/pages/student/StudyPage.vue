<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import ProgressBar from "primevue/progressbar";
import SelectButton from "primevue/selectbutton";
import Tag from "primevue/tag";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { answerCard, myCardSet, studySet, studyToday } from "../../api";
import type { Card as FlashCard, StudyDirection } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { isCloseEnough } from "../../utils/levenshtein";
import { canSpeak, speak } from "../../utils/tts";

const route = useRoute();
const router = useRouter();
const isToday = route.params.id === "today";
const setId = isToday ? null : Number(route.params.id);

const title = ref(isToday ? "Повторение на сегодня" : "…");
const original = ref<FlashCard[]>([]); // карточки сессии в порядке с бэкенда
const queue = ref<FlashCard[]>([]); // рабочая очередь (заваленные уезжают в конец)
const index = ref(0);

const interactionMode = ref<"flip" | "write">("flip");
const direction = ref<StudyDirection>("front_back");
// фактическое направление текущей карточки (для mixed выбирается на карточку)
const cardDir = ref<"front_back" | "back_front">("front_back");

const flipped = ref(false);
const answer = ref("");
const result = ref<"correct" | "wrong" | null>(null);
const sessionCorrect = ref(0);
const sessionWrong = ref(0);
const finished = ref(false);
const speechOn = canSpeak();

const modeOptions = [
  { label: "Карточки", value: "flip" },
  { label: "Печатать ответ", value: "write" },
];
const directionOptions = [
  { label: "EN → RU", value: "front_back" },
  { label: "RU → EN", value: "back_front" },
  { label: "Вперемешку", value: "mixed" },
];

const current = computed<FlashCard | null>(() => queue.value[index.value] ?? null);
const total = computed(() => original.value.length);
const progress = computed(() =>
  total.value ? Math.round((Math.min(index.value, total.value) / total.value) * 100) : 0,
);
// Текст-вопрос и ожидаемый ответ с учётом направления карточки
const prompt = computed(() =>
  !current.value ? "" : cardDir.value === "front_back" ? current.value.front : current.value.back,
);
const expected = computed(() =>
  !current.value ? "" : cardDir.value === "front_back" ? current.value.back : current.value.front,
);
// Английская сторона (front) — её и озвучиваем
const englishText = computed(() => current.value?.front ?? "");

function pickDir() {
  cardDir.value =
    direction.value === "mixed"
      ? Math.random() < 0.5
        ? "front_back"
        : "back_front"
      : direction.value;
}

onMounted(async () => {
  try {
    if (isToday) {
      const t = await studyToday();
      original.value = t.cards;
    } else {
      const [cards, set] = await Promise.all([
        studySet(setId as number, direction.value),
        myCardSet(setId as number),
      ]);
      original.value = cards;
      title.value = set.title;
    }
    restart();
  } catch {
    router.push("/cabinet");
  }
});

function normalize(s: string): string {
  return s.trim().toLowerCase().replace(/ё/g, "е").replace(/\s+/g, " ");
}

function restart() {
  queue.value = [...original.value];
  index.value = 0;
  flipped.value = false;
  finished.value = false;
  sessionCorrect.value = 0;
  sessionWrong.value = 0;
  answer.value = "";
  result.value = null;
  pickDir();
}

function next() {
  flipped.value = false;
  answer.value = "";
  result.value = null;
  if (index.value + 1 >= queue.value.length) {
    finished.value = true;
  } else {
    index.value += 1;
    pickDir();
  }
}

function switchMode(m: "flip" | "write") {
  interactionMode.value = m;
  restart();
}

function switchDirection(d: StudyDirection) {
  direction.value = d;
  restart();
}

/** Записать ответ на бэкенд (SRS), обновить счётчики; заваленную — в конец очереди. */
async function record(ok: boolean) {
  const card = current.value;
  if (!card) return;
  if (ok) sessionCorrect.value += 1;
  else {
    sessionWrong.value += 1;
    queue.value.push(card); // доучить эту же карточку в конце сессии
  }
  try {
    await answerCard(card.id, ok);
  } catch {
    // прогресс не критичен — не мешаем учиться
  }
}

// Режим карточек: после переворота ученик сам отмечает, помнил или нет
async function flipAnswer(ok: boolean) {
  await record(ok);
  next();
}

// Режим ввода: сверяем с прощением одной опечатки
async function check() {
  if (!current.value || result.value !== null) return;
  const ok = isCloseEnough(normalize(answer.value), normalize(expected.value));
  result.value = ok ? "correct" : "wrong";
  await record(ok);
}

// «Всё равно верно» — перебить ошибку как правильный ответ
async function override() {
  if (!current.value) return;
  sessionWrong.value = Math.max(0, sessionWrong.value - 1);
  // убрать карточку, добавленную в конец очереди при ошибке
  const last = queue.value.lastIndexOf(current.value, queue.value.length - 1);
  if (last > index.value) queue.value.splice(last, 1);
  result.value = "correct";
  try {
    await answerCard(current.value.id, true);
  } catch {
    /* не критично */
  }
}
</script>

<template>
  <AppLayout>
    <Card class="study-card">
      <template #title>
        <div class="head">
          <Button icon="pi pi-arrow-left" text rounded @click="router.push('/cabinet')" />
          <span class="title-text">{{ title }}</span>
        </div>
        <div class="modes">
          <SelectButton
            :model-value="interactionMode"
            :options="modeOptions"
            option-label="label"
            option-value="value"
            :allow-empty="false"
            @update:model-value="switchMode"
          />
          <SelectButton
            :model-value="direction"
            :options="directionOptions"
            option-label="label"
            option-value="value"
            :allow-empty="false"
            @update:model-value="switchDirection"
          />
        </div>
      </template>
      <template #content>
        <p v-if="!total" class="hint">Карточек к повторению нет — всё выучено на сегодня! 🎉</p>

        <template v-else-if="finished">
          <div class="finish">
            <h3>Готово! 🎉</h3>
            <p>Правильно: {{ sessionCorrect }} из {{ sessionCorrect + sessionWrong }}</p>
            <Button label="Ещё раз" icon="pi pi-replay" @click="restart" />
          </div>
        </template>

        <template v-else-if="current">
          <ProgressBar :value="progress" :show-value="false" class="bar" />
          <p class="counter">{{ Math.min(index + 1, total) }} / {{ total }}</p>

          <!-- Режим карточек -->
          <template v-if="interactionMode === 'flip'">
            <button class="flashcard" type="button" @click="flipped = !flipped">
              <span class="word">{{ flipped ? expected : prompt }}</span>
              <span
                v-if="flipped && current.example"
                class="example"
              >{{ current.example }}</span>
              <span class="flip-hint">{{ flipped ? "перевод" : "нажми, чтобы перевернуть" }}</span>
            </button>
            <div class="controls">
              <Button
                v-if="speechOn"
                icon="pi pi-volume-up"
                label="Озвучить"
                severity="secondary"
                text
                @click="speak(englishText)"
              />
              <div v-if="flipped" class="judge">
                <Button label="Не помнил" severity="danger" outlined @click="flipAnswer(false)" />
                <Button label="Помнил" severity="success" @click="flipAnswer(true)" />
              </div>
              <Button v-else label="Показать ответ" @click="flipped = true" />
            </div>
          </template>

          <!-- Режим ввода -->
          <template v-else>
            <div class="write-box">
              <div class="prompt-row">
                <span class="word">{{ prompt }}</span>
                <Button
                  v-if="speechOn && cardDir === 'front_back'"
                  icon="pi pi-volume-up"
                  rounded
                  text
                  @click="speak(englishText)"
                />
              </div>
              <InputText
                v-model="answer"
                placeholder="Ваш ответ"
                :disabled="result !== null"
                autofocus
                fluid
                @keyup.enter="result === null ? check() : next()"
              />
              <Tag
                v-if="result === 'correct'"
                :value="answer.trim().toLowerCase() === expected.toLowerCase() ? 'Верно!' : `Почти — засчитано (${expected})`"
                severity="success"
                class="result"
              />
              <template v-else-if="result === 'wrong'">
                <Tag :value="`Неверно. Правильно: ${expected}`" severity="danger" class="result" />
                <Button label="Всё равно верно" size="small" text @click="override" />
              </template>
              <p v-if="result !== null && current.example" class="example">{{ current.example }}</p>
              <div class="controls">
                <Button
                  v-if="speechOn && cardDir === 'back_front' && result !== null"
                  icon="pi pi-volume-up"
                  label="Озвучить"
                  severity="secondary"
                  text
                  @click="speak(englishText)"
                />
                <Button
                  v-if="result === null"
                  label="Проверить"
                  :disabled="!answer.trim()"
                  @click="check"
                />
                <Button v-else label="Дальше" icon="pi pi-chevron-right" icon-pos="right" @click="next" />
              </div>
            </div>
          </template>
        </template>
      </template>
    </Card>
  </AppLayout>
</template>

<style scoped>
.study-card {
  max-width: 38rem;
  margin: 0 auto;
}
.head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.title-text {
  font-weight: 600;
}
.modes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.6rem;
}
.bar {
  height: 6px;
}
.counter {
  text-align: center;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
  margin: 0.5rem 0;
}
.flashcard {
  width: 100%;
  min-height: 14rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  border: 2px solid var(--p-surface-300);
  border-radius: 12px;
  background: var(--p-surface-0);
  cursor: pointer;
  font: inherit;
}
.flashcard:hover {
  border-color: var(--p-primary-color);
}
.word {
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
  padding: 0 1rem;
}
.example {
  font-size: 0.95rem;
  font-style: italic;
  color: var(--p-text-muted-color);
  text-align: center;
}
.flip-hint {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
.controls {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 1rem;
  gap: 0.75rem;
}
.judge {
  display: flex;
  gap: 0.75rem;
}
.write-box {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: stretch;
  padding: 1rem 0;
}
.prompt-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}
.result {
  align-self: center;
}
.finish {
  text-align: center;
  padding: 2rem 0;
}
.hint {
  color: var(--p-text-muted-color);
  text-align: center;
  padding: 1.5rem 0;
}
</style>
