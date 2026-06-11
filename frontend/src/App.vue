<script setup lang="ts">
import Toast from "primevue/toast";
import ConfirmDialog from "primevue/confirmdialog";
</script>

<template>
  <Toast position="top-right" />
  <ConfirmDialog />
  <router-view />
</template>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--p-surface-50);
}
</style>
