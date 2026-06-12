<script setup lang="ts">
import { computed } from "vue";

import { balanceInfo } from "../utils/balance";
import { formatMoney } from "../utils/format";

const props = defineProps<{ debt: string | number; lessonPrice: string | number }>();

const info = computed(() => balanceInfo(props.debt, props.lessonPrice));
</script>

<template>
  <span v-if="info.kind === 'debt'" class="debt">Долг {{ formatMoney(info.amount) }}</span>
  <span v-else-if="info.kind === 'prepaid'" class="prepaid">
    Предоплата {{ formatMoney(info.amount) }}
    <template v-if="info.lessonsLeft !== null">
      ({{ info.lessonsLeft }} {{ lessonWord(info.lessonsLeft) }})
    </template>
    <i
      v-if="info.renewalDue"
      v-tooltip="'Предоплата заканчивается — пора продлевать'"
      class="pi pi-exclamation-triangle warn"
    />
  </span>
  <span v-else class="zero">—</span>
</template>

<script lang="ts">
export function lessonWord(n: number): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return "урок";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return "урока";
  return "уроков";
}
export default {};
</script>

<style scoped>
.debt {
  color: var(--p-red-600);
  font-weight: 600;
}
.prepaid {
  color: var(--p-green-600);
  font-weight: 600;
}
.zero {
  color: var(--p-text-muted-color);
}
.warn {
  color: var(--p-amber-500);
  margin-left: 0.3rem;
}
</style>
