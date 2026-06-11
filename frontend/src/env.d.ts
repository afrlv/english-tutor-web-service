/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<object, object, unknown>;
  export default component;
}

declare module "primelocale/js/ru.js" {
  export const ru: Record<string, unknown>;
}
