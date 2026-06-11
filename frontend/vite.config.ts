/// <reference types="vitest/config" />
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

const backend = process.env.BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": backend,
      "/media": backend,
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
