<script setup lang="ts">
import Button from "primevue/button";

import { attachmentKind, videoEmbedUrl, type AttachmentLike } from "../utils/attachments";

// Подходит и для вложений ДЗ, и для материалов урока
defineProps<{ attachments: AttachmentLike[]; removable?: boolean }>();
const emit = defineEmits<{ remove: [id: number] }>();

function href(a: AttachmentLike): string {
  return a.url ?? `/api/files/${a.file_path}`;
}
</script>

<template>
  <div v-if="attachments.length" class="list">
    <div v-for="a in attachments" :key="a.id" class="entry">
      <!-- Изображение: превью, клик — полный размер -->
      <template v-if="attachmentKind(a) === 'image'">
        <figure class="media">
          <a :href="href(a)" target="_blank" rel="noopener">
            <img :src="href(a)" :alt="a.name" class="thumb" />
          </a>
          <figcaption>{{ a.name }}</figcaption>
        </figure>
      </template>

      <!-- Аудио: плеер -->
      <template v-else-if="attachmentKind(a) === 'audio'">
        <figure class="media">
          <audio :src="href(a)" controls preload="none" class="audio" />
          <figcaption>{{ a.name }}</figcaption>
        </figure>
      </template>

      <!-- Видео-ссылка (YouTube/Vimeo): встроенный плеер -->
      <template v-else-if="attachmentKind(a) === 'video'">
        <figure class="media">
          <div class="video-wrap">
            <iframe
              :src="videoEmbedUrl(a.url!) ?? ''"
              class="video"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
            />
          </div>
          <figcaption>{{ a.name }}</figcaption>
        </figure>
      </template>

      <!-- Прочее (PDF, файлы, обычные ссылки): ссылка с иконкой -->
      <span v-else class="item">
        <i :class="a.url ? 'pi pi-link' : 'pi pi-paperclip'" />
        <a :href="href(a)" target="_blank" rel="noopener">{{ a.name }}</a>
      </span>

      <Button
        v-if="removable"
        v-tooltip="'Удалить'"
        icon="pi pi-times"
        text
        rounded
        size="small"
        severity="danger"
        class="remove"
        @click="emit('remove', a.id)"
      />
    </div>
  </div>
</template>

<style scoped>
.list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.25rem;
}
.entry {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.2rem;
}
.media {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-width: 18rem;
}
.media figcaption {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  word-break: break-word;
}
.thumb {
  max-width: 18rem;
  max-height: 12rem;
  border-radius: 8px;
  border: 1px solid var(--p-surface-200);
  object-fit: cover;
  cursor: zoom-in;
  display: block;
}
.audio {
  width: 18rem;
  height: 2.5rem;
}
.video-wrap {
  position: relative;
  width: 20rem;
  aspect-ratio: 16 / 9;
}
.video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: 8px;
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
.remove {
  flex-shrink: 0;
}
</style>
