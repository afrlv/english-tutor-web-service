// Определение типа вложения для отображения (превью/плеер) и встраивание видео.

export type AttachmentKind = "image" | "audio" | "video" | "pdf" | "file";

export interface AttachmentLike {
  id: number;
  name: string;
  file_path: string | null;
  url: string | null;
}

const IMAGE_EXT = ["jpg", "jpeg", "png", "webp", "gif"];
const AUDIO_EXT = ["mp3", "m4a", "ogg", "wav"];

function ext(s: string | null): string {
  if (!s) return "";
  const m = s.toLowerCase().match(/\.([a-z0-9]+)(?:\?|#|$)/);
  return m ? m[1] : "";
}

/**
 * Встраиваемый URL плеера для ссылок YouTube/Vimeo, иначе null.
 * Поддержка: youtube.com/watch?v=, youtu.be/, youtube.com/shorts/, vimeo.com/<id>.
 */
export function videoEmbedUrl(url: string): string | null {
  let m = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([\w-]{11})/);
  if (m) return `https://www.youtube.com/embed/${m[1]}`;
  m = url.match(/vimeo\.com\/(\d+)/);
  if (m) return `https://player.vimeo.com/video/${m[1]}`;
  return null;
}

/** Тип вложения: загруженный файл — по расширению, ссылка на видео — video. */
export function attachmentKind(a: AttachmentLike): AttachmentKind {
  if (a.file_path) {
    const e = ext(a.file_path) || ext(a.name);
    if (IMAGE_EXT.includes(e)) return "image";
    if (AUDIO_EXT.includes(e)) return "audio";
    if (e === "pdf") return "pdf";
    return "file";
  }
  if (a.url && videoEmbedUrl(a.url)) return "video";
  return "file";
}
