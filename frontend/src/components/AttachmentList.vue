<script setup lang="ts">
import Button from "primevue/button";

// Подходит и для вложений ДЗ, и для материалов урока
interface AttachmentLike {
  id: number;
  name: string;
  file_path: string | null;
  url: string | null;
}

defineProps<{ attachments: AttachmentLike[]; removable?: boolean }>();
const emit = defineEmits<{ remove: [id: number] }>();

function href(a: AttachmentLike): string {
  return a.url ?? `/media/${a.file_path}`;
}
</script>

<template>
  <div v-if="attachments.length" class="list">
    <span v-for="a in attachments" :key="a.id" class="item">
      <i :class="a.url ? 'pi pi-link' : 'pi pi-paperclip'" />
      <a :href="href(a)" target="_blank" rel="noopener">{{ a.name }}</a>
      <Button
        v-if="removable"
        icon="pi pi-times"
        text
        rounded
        size="small"
        severity="danger"
        @click="emit('remove', a.id)"
      />
    </span>
  </div>
</template>

<style scoped>
.list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.25rem;
}
.item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.9rem;
  background: var(--p-surface-100);
  border-radius: 6px;
  padding: 0.1rem 0.5rem;
}
</style>
