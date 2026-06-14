import { describe, expect, it } from "vitest";

import { attachmentKind, videoEmbedUrl } from "./attachments";

const att = (over: Partial<Parameters<typeof attachmentKind>[0]>) => ({
  id: 1,
  name: "x",
  file_path: null,
  url: null,
  ...over,
});

describe("videoEmbedUrl", () => {
  it("youtube watch", () => {
    expect(videoEmbedUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ")).toBe(
      "https://www.youtube.com/embed/dQw4w9WgXcQ",
    );
  });
  it("youtu.be короткий", () => {
    expect(videoEmbedUrl("https://youtu.be/dQw4w9WgXcQ")).toBe(
      "https://www.youtube.com/embed/dQw4w9WgXcQ",
    );
  });
  it("youtube shorts", () => {
    expect(videoEmbedUrl("https://youtube.com/shorts/dQw4w9WgXcQ")).toBe(
      "https://www.youtube.com/embed/dQw4w9WgXcQ",
    );
  });
  it("vimeo", () => {
    expect(videoEmbedUrl("https://vimeo.com/123456789")).toBe(
      "https://player.vimeo.com/video/123456789",
    );
  });
  it("не видео — null", () => {
    expect(videoEmbedUrl("https://example.com/page")).toBeNull();
  });
});

describe("attachmentKind", () => {
  it("картинка по расширению file_path", () => {
    expect(attachmentKind(att({ file_path: "lesson/abc.png", name: "фото.png" }))).toBe("image");
    expect(attachmentKind(att({ file_path: "lesson/abc.webp" }))).toBe("image");
  });
  it("аудио по расширению", () => {
    expect(attachmentKind(att({ file_path: "homework/x.mp3" }))).toBe("audio");
    expect(attachmentKind(att({ file_path: "homework/x.ogg" }))).toBe("audio");
  });
  it("pdf — отдельный тип", () => {
    expect(attachmentKind(att({ file_path: "lesson/doc.pdf" }))).toBe("pdf");
  });
  it("видео-ссылка — video", () => {
    expect(attachmentKind(att({ url: "https://youtu.be/dQw4w9WgXcQ" }))).toBe("video");
  });
  it("обычная ссылка — file", () => {
    expect(attachmentKind(att({ url: "https://example.com/article" }))).toBe("file");
  });
});
