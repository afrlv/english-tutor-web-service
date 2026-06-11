<script setup lang="ts">
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { financeSummary } from "../../api";
import type { FinanceSummary } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { formatMoney } from "../../utils/format";

const router = useRouter();
const summary = ref<FinanceSummary | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    summary.value = await financeSummary();
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <AppLayout>
    <Card class="mb">
      <template #title>Заработано всего</template>
      <template #content>
        <span class="total">{{ formatMoney(summary?.total_earned ?? 0) }}</span>
      </template>
    </Card>
    <Card>
      <template #title>По ученикам</template>
      <template #content>
        <DataTable
          :value="summary?.students ?? []"
          :loading="loading"
          selection-mode="single"
          @row-select="(e) => router.push(`/students/${e.data.student_id}`)"
        >
          <template #empty>Пока нет данных</template>
          <Column field="student_name" header="Ученик" />
          <Column header="Заработано">
            <template #body="{ data }">{{ formatMoney(data.earned) }}</template>
          </Column>
          <Column header="Оплачено">
            <template #body="{ data }">{{ formatMoney(data.paid) }}</template>
          </Column>
          <Column header="Долг">
            <template #body="{ data }">
              <span :class="{ debt: parseFloat(data.debt) > 0 }">{{ formatMoney(data.debt) }}</span>
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </AppLayout>
</template>

<style scoped>
.total {
  font-size: 2rem;
  font-weight: 600;
}
.mb {
  margin-bottom: 1rem;
}
.debt {
  color: var(--p-red-500);
  font-weight: 600;
}
</style>
