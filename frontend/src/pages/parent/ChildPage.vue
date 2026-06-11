<script setup lang="ts">
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Tag from "primevue/tag";
import { onMounted, ref } from "vue";

import { fetchChild } from "../../api";
import type { ChildCard } from "../../api/types";
import AppLayout from "../../components/AppLayout.vue";
import { formatDateTime, formatMoney } from "../../utils/format";

const child = ref<ChildCard | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    child.value = await fetchChild();
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <AppLayout>
    <div class="grid">
      <Card>
        <template #title>{{ child?.student.full_name ?? "…" }}</template>
        <template #content>
          <p>
            Стоимость урока:
            <strong>{{ formatMoney(child?.lesson_price ?? 0) }}</strong>
          </p>
          <div v-if="child?.recommendations">
            <h4>Рекомендации учителя</h4>
            <p class="recommendations">{{ child.recommendations }}</p>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Расписание уроков</template>
        <template #content>
          <DataTable :value="child?.lessons ?? []" :loading="loading">
            <template #empty>Уроков пока нет</template>
            <Column header="Когда">
              <template #body="{ data }">{{ formatDateTime(data.scheduled_at) }}</template>
            </Column>
            <Column field="topic" header="Тема" />
            <Column field="recommendation" header="Рекомендации" />
            <Column header="Статус">
              <template #body="{ data }">
                <Tag
                  :value="
                    data.status === 'conducted'
                      ? 'Проведён'
                      : data.status === 'cancelled'
                        ? 'Отменён'
                        : 'Запланирован'
                  "
                  :severity="
                    data.status === 'conducted'
                      ? 'success'
                      : data.status === 'cancelled'
                        ? 'danger'
                        : 'info'
                  "
                />
              </template>
            </Column>
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
.recommendations {
  white-space: pre-wrap;
}
</style>
