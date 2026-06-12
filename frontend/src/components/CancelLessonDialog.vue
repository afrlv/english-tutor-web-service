<script setup lang="ts">
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputNumber from "primevue/inputnumber";
import RadioButton from "primevue/radiobutton";
import Textarea from "primevue/textarea";
import { ref, watch } from "vue";

export type CancelKind = "teacher" | "student" | "late";

const visible = defineModel<boolean>("visible", { required: true });
const emit = defineEmits<{
  confirm: [kind: CancelKind, comment: string | null, chargeAmount: string | null];
}>();

const kind = ref<CancelKind>("teacher");
const comment = ref("");
const amount = ref<number | null>(null);

const options: { value: CancelKind; label: string; hint: string }[] = [
  { value: "teacher", label: "Отменяет учитель", hint: "без оплаты" },
  { value: "student", label: "Ученик предупредил заранее", hint: "без оплаты" },
  { value: "late", label: "Поздняя отмена / неявка", hint: "с оплатой" },
];

watch(visible, (open) => {
  if (!open) return;
  kind.value = "teacher";
  comment.value = "";
  amount.value = null;
});

function submit() {
  emit(
    "confirm",
    kind.value,
    comment.value.trim() || null,
    kind.value === "late" && amount.value ? String(amount.value) : null,
  );
}
</script>

<template>
  <Dialog v-model:visible="visible" header="Отмена урока" modal>
    <form class="form" @submit.prevent="submit">
      <div v-for="opt in options" :key="opt.value" class="option">
        <RadioButton v-model="kind" :input-id="`ck-${opt.value}`" :value="opt.value" />
        <label :for="`ck-${opt.value}`">
          {{ opt.label }} <span class="hint">— {{ opt.hint }}</span>
        </label>
      </div>

      <label v-if="kind === 'late'" class="field">
        Сумма начисления (пусто — полная стоимость урока)
        <InputNumber
          v-model="amount"
          :min="0"
          mode="currency"
          currency="RUB"
          locale="ru-RU"
          fluid
        />
      </label>

      <label class="field">
        Комментарий (необязательно)
        <Textarea v-model="comment" rows="2" fluid />
      </label>

      <Button type="submit" label="Отменить урок" severity="danger" />
    </form>
  </Dialog>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 24rem;
}
.option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.hint {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}
</style>
