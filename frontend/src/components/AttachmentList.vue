<script setup lang="ts">
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import { ref } from "vue";

import { attachmentKind, videoEmbedUrl, type AttachmentLike } from "../utils/attachments";

// Подходит и для вложений ДЗ, и для материалов урока
defineProps<{ attachments: AttachmentLike[]; removable?: boolean }>();
const emit = defineEmits<{ remove: [id: number] }>();

function href(a: AttachmentLike): string {
  return a.url ?? `/api/files/${a.file_path}`;
}

// Просмотр PDF в модалке
const pdfOpen = ref(false);
const pdfUrl = ref("");
const pdfName = ref("");

function openPdf(a: AttachmentLike) {
  pdfUrl.value = href(a);
  pdfName.value = a.name;
  pdfOpen.value = true;
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

      <!-- PDF: превью-плитка, клик — просмотр в модалке -->
      <template v-else-if="attachmentKind(a) === 'pdf'">
        <button type="button" class="pdf-tile" @click="openPdf(a)">
          <i class="pi pi-file-pdf" />
          <span class="pdf-name">{{ a.name }}</span>
        </button>
      </template>

      <!-- Прочее (файлы, обычные ссылки): плитка с иконкой и подписью -->
      <a v-else :href="href(a)" target="_blank" rel="noopener" class="tile">
        <i :class="a.url ? 'pi pi-external-link' : 'pi pi-file'" />
        <span class="tile-name">{{ a.name }}</span>
      </a>

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

  <Dialog
    v-model:visible="pdfOpen"
    :header="pdfName"
    modal
    maximizable
    dismissable-mask
    class="pdf-dialog"
    :style="{ width: '80vw', height: '90vh' }"
  >
    <iframe :src="pdfUrl" class="pdf-frame" title="PDF" />
  </Dialog>
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
.pdf-tile,
.tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  width: 9rem;
  height: 7rem;
  padding: 0.75rem;
  border: 1px solid var(--p-surface-200);
  border-radius: 8px;
  background: var(--p-surface-0);
  cursor: pointer;
  font: inherit;
  text-decoration: none;
}
.pdf-tile:hover,
.tile:hover {
  border-color: var(--p-primary-color);
}
.pdf-tile .pi-file-pdf {
  font-size: 2.2rem;
  color: #d32f2f;
}
.tile .pi {
  font-size: 2.2rem;
  color: var(--p-primary-color);
}
.pdf-name,
.tile-name {
  font-size: 0.8rem;
  text-align: center;
  word-break: break-word;
  color: var(--p-text-color);
  line-height: 1.2;
  max-height: 2.4em;
  overflow: hidden;
}
.pdf-frame {
  width: 100%;
  height: 100%;
  border: none;
}
:deep(.pdf-dialog .p-dialog-content) {
  height: 100%;
  padding: 0;
}
.remove {
  flex-shrink: 0;
}
</style>
