<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import ProgressBar from "primevue/progressbar";
import SelectButton from "primevue/selectbutton";
import Tag from "primevue/tag";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { answerCard, myCardSet } from "../../api";
import type { Card as FlashCard, CardSet } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";

const route = useRoute();
const router = useRouter();
const setId = Number(route.params.id);

const cardSet = ref<CardSet | null>(null);
const mode = ref<"flip" | "write">("flip");
const index = ref(0);
const flipped = ref(false);
// режим письма
const answer = ref("");
const result = ref<"correct" | "wrong" | null>(null);
const sessionCorrect = ref(0);
const sessionWrong = ref(0);
const finished = ref(false);

const modeOptions = [
  { label: "Карточки", value: "flip" },
  { label: "Печатать ответ", value: "write" },
];

const cards = computed<FlashCard[]>(() => cardSet.value?.cards ?? []);
const current = computed(() => cards.value[index.value] ?? null);
const progress = computed(() =>
  cards.value.length ? Math.round((index.value / cards.value.length) * 100) : 0,
);

onMounted(async () => {
  try {
    cardSet.value = await myCardSet(setId);
  } catch {
    router.push("/cabinet");
  }
});

function normalize(s: string): string {
  return s.trim().toLowerCase().replace(/ё/g, "е").replace(/\s+/g, " ");
}

function next() {
  flipped.value = false;
  answer.value = "";
  result.value = null;
  if (index.value + 1 >= cards.value.length) {
    finished.value = true;
  } else {
    index.value += 1;
  }
}

function restart() {
  index.value = 0;
  flipped.value = false;
  finished.value = false;
  sessionCorrect.value = 0;
  sessionWrong.value = 0;
  answer.value = "";
  result.value = null;
}

function switchMode(m: "flip" | "write") {
  mode.value = m;
  restart();
}

async function check() {
  if (!current.value || result.value !== null) return;
  const ok = normalize(answer.value) === normalize(current.value.back);
  result.value = ok ? "correct" : "wrong";
  if (ok) sessionCorrect.value += 1;
  else sessionWrong.value += 1;
  try {
    await answerCard(current.value.id, ok);
  } catch {
    // прогресс не критичен — не мешаем учиться
  }
}
</script>

<template>
  <AppLayout>
    <Card class="study-card">
      <template #title>
        <div class="head">
          <Button icon="pi pi-arrow-left" text rounded @click="router.push('/cabinet')" />
          {{ cardSet?.title ?? "…" }}
          <SelectButton
            :model-value="mode"
            :options="modeOptions"
            option-label="label"
            option-value="value"
            :allow-empty="false"
            class="mode"
            @update:model-value="switchMode"
          />
        </div>
      </template>
      <template #content>
        <p v-if="!cards.length" class="hint">В этом наборе пока нет карточек.</p>

        <template v-else-if="finished">
          <div class="finish">
            <h3>Готово! 🎉</h3>
            <p v-if="mode === 'write'">
              Правильно: {{ sessionCorrect }} из {{ sessionCorrect + sessionWrong }}
            </p>
            <Button label="Ещё раз" icon="pi pi-replay" @click="restart" />
          </div>
        </template>

        <template v-else-if="current">
          <ProgressBar :value="progress" :show-value="false" class="bar" />
          <p class="counter">{{ index + 1 }} / {{ cards.length }}</p>

          <!-- Режим листания -->
          <template v-if="mode === 'flip'">
            <button class="flashcard" type="button" @click="flipped = !flipped">
              <span class="word">{{ flipped ? current.back : current.front }}</span>
              <span class="flip-hint">{{ flipped ? "перевод" : "нажми, чтобы перевернуть" }}</span>
            </button>
            <div class="controls">
              <Button
                label="Назад"
                icon="pi pi-chevron-left"
                severity="secondary"
                :disabled="index === 0"
                @click="index -= 1; flipped = false"
              />
              <Button label="Дальше" icon="pi pi-chevron-right" icon-pos="right" @click="next" />
            </div>
          </template>

          <!-- Режим ввода -->
          <template v-else>
            <div class="write-box">
              <span class="word">{{ current.front }}</span>
              <InputText
                v-model="answer"
                placeholder="Перевод"
                :disabled="result !== null"
                autofocus
                fluid
                @keyup.enter="result === null ? check() : next()"
              />
              <Tag
                v-if="result === 'correct'"
                value="Верно!"
                severity="success"
                class="result"
              />
              <Tag
                v-else-if="result === 'wrong'"
                :value="`Неверно. Правильно: ${current.back}`"
                severity="danger"
                class="result"
              />
              <div class="controls">
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
.mode {
  margin-left: auto;
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
.flip-hint {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
.controls {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  gap: 0.5rem;
}
.write-box {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: stretch;
  padding: 1rem 0;
}
.write-box .word {
  text-align: center;
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
}
</style>
