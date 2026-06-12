<script setup lang="ts">
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Message from "primevue/message";
import Tag from "primevue/tag";
import { computed, onMounted, ref } from "vue";

import { fetchBalance } from "../../api";
import type { Balance } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { lessonWord } from "../../components/BalanceCell.vue";
import { balanceInfo } from "../../utils/balance";
import { formatDateTime, formatMoney } from "../../utils/format";

const balance = ref<Balance | null>(null);
const loading = ref(true);

const info = computed(() =>
  balance.value ? balanceInfo(balance.value.debt, balance.value.lesson_price) : null,
);

onMounted(async () => {
  try {
    balance.value = await fetchBalance();
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <AppLayout>
    <div class="grid">
      <Card>
        <template #title>Оплата уроков</template>
        <template #content>
          <Message v-if="info?.kind === 'debt'" severity="warn" class="mb">
            Задолженность {{ formatMoney(info.amount) }} — пожалуйста, оплатите занятия.
          </Message>
          <Message v-else-if="info?.renewalDue" severity="info" class="mb">
            Осталось {{ info.lessonsLeft }} {{ lessonWord(info.lessonsLeft ?? 0) }} по
            предоплате — пора продлевать.
          </Message>

          <div class="stats">
            <div>
              <div class="label">Стоимость урока</div>
              <div class="value">{{ formatMoney(balance?.lesson_price ?? 0) }}</div>
            </div>
            <div>
              <div class="label">Начислено</div>
              <div class="value">{{ formatMoney(balance?.charged ?? 0) }}</div>
            </div>
            <div>
              <div class="label">Оплачено</div>
              <div class="value">{{ formatMoney(balance?.paid ?? 0) }}</div>
            </div>
            <div v-if="info?.kind === 'prepaid'">
              <div class="label">Предоплачено</div>
              <div class="value prepaid">
                {{ formatMoney(info.amount) }}
                <span v-if="info.lessonsLeft !== null" class="lessons">
                  ≈ {{ info.lessonsLeft }} {{ lessonWord(info.lessonsLeft) }}
                </span>
              </div>
            </div>
            <div v-else>
              <div class="label">Задолженность</div>
              <div class="value" :class="{ debt: info?.kind === 'debt' }">
                {{ formatMoney(info?.kind === 'debt' ? info.amount : 0) }}
              </div>
            </div>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>История операций</template>
        <template #content>
          <DataTable :value="balance?.transactions ?? []" :loading="loading">
            <template #empty>Операций пока нет</template>
            <Column header="Дата">
              <template #body="{ data }">{{ formatDateTime(data.created_at) }}</template>
            </Column>
            <Column header="Тип">
              <template #body="{ data }">
                <Tag
                  :value="data.type === 'charge' ? 'Урок' : 'Оплата'"
                  :severity="data.type === 'charge' ? 'warn' : 'success'"
                />
              </template>
            </Column>
            <Column header="Сумма">
              <template #body="{ data }">{{ formatMoney(data.amount) }}</template>
            </Column>
            <Column field="comment" header="Комментарий" />
          </DataTable>
        </template>
      </Card>
    </div>
  </AppLayout>
</template>

<style scoped>
.grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.stats {
  display: flex;
  gap: 2.5rem;
  flex-wrap: wrap;
}
.label {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
.value {
  font-size: 1.4rem;
  font-weight: 600;
}
.debt {
  color: var(--p-red-500);
}
.prepaid {
  color: var(--p-green-600);
}
.lessons {
  font-size: 0.95rem;
  font-weight: 400;
  color: var(--p-text-muted-color);
}
.mb {
  margin-bottom: 1rem;
}
</style>
