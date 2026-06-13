<script setup lang="ts">
import Card from "primevue/card";
import { computed } from "vue";

import type { DashboardStats } from "../api/types";
import { formatMoney } from "../utils/format";

const props = defineProps<{ stats: DashboardStats }>();

// Динамика заработка к прошлому месяцу
const trend = computed(() => {
  const cur = parseFloat(props.stats.earned_this_month);
  const prev = parseFloat(props.stats.earned_prev_month);
  if (prev === 0) return null;
  return Math.round(((cur - prev) / prev) * 100);
});

const maxMonth = computed(() =>
  Math.max(1, ...props.stats.monthly.map((m) => parseFloat(m.earned))),
);

function barHeight(earned: string): number {
  return Math.round((parseFloat(earned) / maxMonth.value) * 100);
}

function monthLabel(key: string): string {
  const names = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
  return names[parseInt(key.slice(5, 7), 10) - 1];
}
</script>

<template>
  <div class="metrics">
    <Card class="metric">
      <template #content>
        <div class="label">Заработано в этом месяце</div>
        <div class="value">{{ formatMoney(stats.earned_this_month) }}</div>
        <div v-if="trend !== null" class="trend" :class="{ up: trend >= 0, down: trend < 0 }">
          <i :class="trend >= 0 ? 'pi pi-arrow-up' : 'pi pi-arrow-down'" />
          {{ Math.abs(trend) }}% к прошлому
        </div>
        <div v-else class="trend muted">за месяц</div>
      </template>
    </Card>

    <Card class="metric">
      <template #content>
        <div class="label">Задолженность учеников</div>
        <div class="value" :class="{ debt: parseFloat(stats.debt_total) > 0 }">
          {{ formatMoney(stats.debt_total) }}
        </div>
        <div class="trend muted">всего за всё время {{ formatMoney(stats.earned_total) }}</div>
      </template>
    </Card>

    <Card class="metric">
      <template #content>
        <div class="label">Ученики</div>
        <div class="value">{{ stats.students_active }} / {{ stats.students_total }}</div>
        <div class="trend muted">
          активны за 30 дней<template v-if="stats.students_quiet">
            · <span class="quiet">затихли: {{ stats.students_quiet }}</span></template>
        </div>
      </template>
    </Card>

    <Card class="metric">
      <template #content>
        <div class="label">Уроки на этой неделе</div>
        <div class="value">{{ stats.lessons_week_conducted }} / {{ stats.lessons_week_conducted + stats.lessons_week_planned }}</div>
        <div class="trend muted">проведено · в месяце {{ stats.lessons_month_conducted }}</div>
      </template>
    </Card>

    <Card class="metric chart-card">
      <template #content>
        <div class="label">Заработок по месяцам</div>
        <div class="chart">
          <div v-for="m in stats.monthly" :key="m.month" class="bar-col">
            <div
              v-tooltip.top="formatMoney(m.earned)"
              class="bar"
              :style="{ height: barHeight(m.earned) + '%' }"
            />
            <span class="bar-label">{{ monthLabel(m.month) }}</span>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}
.metric :deep(.p-card-content) {
  padding: 0.25rem 0;
}
.label {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
.value {
  font-size: 1.6rem;
  font-weight: 700;
  margin: 0.15rem 0;
}
.value.debt {
  color: var(--p-red-500);
}
.trend {
  font-size: 0.8rem;
}
.trend.up {
  color: var(--p-green-600);
}
.trend.down {
  color: var(--p-red-500);
}
.trend.muted {
  color: var(--p-text-muted-color);
}
.quiet {
  color: var(--p-amber-600);
}
.chart-card {
  grid-column: span 2;
}
.chart {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  height: 5rem;
  margin-top: 0.5rem;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  gap: 0.2rem;
}
.bar {
  width: 70%;
  min-height: 2px;
  background: var(--p-primary-color);
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
}
.bar-label {
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
}
</style>
