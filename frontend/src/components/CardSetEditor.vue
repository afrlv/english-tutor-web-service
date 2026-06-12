<script setup lang="ts">
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import { ref } from "vue";

import { addCard, deleteCard, getCardSet, updateCard } from "../api";
import type { Card, CardSet } from "../api/types";

const props = defineProps<{ cardSet: CardSet }>();
const emit = defineEmits<{ changed: [] }>();

const cards = ref<Card[]>([...props.cardSet.cards]);
const newFront = ref("");
const newBack = ref("");
// id карточки в режиме правки
const editingId = ref<number | null>(null);
const editFront = ref("");
const editBack = ref("");

async function refresh() {
  cards.value = (await getCardSet(props.cardSet.id)).cards;
  emit("changed");
}

async function onAdd() {
  if (!newFront.value.trim() || !newBack.value.trim()) return;
  await addCard(props.cardSet.id, newFront.value.trim(), newBack.value.trim());
  newFront.value = "";
  newBack.value = "";
  await refresh();
}

function startEdit(card: Card) {
  editingId.value = card.id;
  editFront.value = card.front;
  editBack.value = card.back;
}

async function saveEdit() {
  if (editingId.value === null) return;
  await updateCard(editingId.value, editFront.value.trim(), editBack.value.trim());
  editingId.value = null;
  await refresh();
}

async function onDelete(id: number) {
  await deleteCard(id);
  await refresh();
}
</script>

<template>
  <div class="editor">
    <div v-for="card in cards" :key="card.id" class="card-row">
      <template v-if="editingId === card.id">
        <InputText v-model="editFront" class="cell" @keyup.enter="saveEdit" />
        <InputText v-model="editBack" class="cell" @keyup.enter="saveEdit" />
        <Button icon="pi pi-check" text rounded size="small" severity="success" @click="saveEdit" />
      </template>
      <template v-else>
        <span class="cell front">{{ card.front }}</span>
        <span class="cell">{{ card.back }}</span>
        <span class="stats" :title="`верно: ${card.times_correct}, ошибок: ${card.times_wrong}`">
          {{ card.times_correct }}✓ {{ card.times_wrong }}✗
        </span>
        <Button icon="pi pi-pencil" text rounded size="small" @click="startEdit(card)" />
        <Button
          icon="pi pi-times"
          text
          rounded
          size="small"
          severity="danger"
          @click="onDelete(card.id)"
        />
      </template>
    </div>
    <p v-if="!cards.length" class="empty">Карточек пока нет</p>

    <form class="card-row add-row" @submit.prevent="onAdd">
      <InputText v-model="newFront" placeholder="Слово (англ.)" class="cell" />
      <InputText v-model="newBack" placeholder="Перевод" class="cell" />
      <Button
        type="submit"
        icon="pi pi-plus"
        label="Добавить"
        size="small"
        :disabled="!newFront.trim() || !newBack.trim()"
      />
    </form>
  </div>
</template>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.card-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.cell {
  flex: 1;
  min-width: 0;
}
.front {
  font-weight: 600;
}
.stats {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}
.add-row {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--p-surface-200);
}
.empty {
  color: var(--p-text-muted-color);
}
</style>
