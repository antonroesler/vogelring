<template>
  <header class="page-header">
    <div class="page-header__text">
      <div class="d-flex align-center ga-3">
        <span v-if="icon" class="icon-tile icon-tile--lg" aria-hidden="true"><v-icon>{{ icon }}</v-icon></span>
        <h1 class="page-title">{{ title }}</h1>
        <slot name="title-append" />
      </div>
      <p v-if="subtitle || $slots.subtitle" class="page-sub"><slot name="subtitle">{{ subtitle }}</slot></p>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; icon?: string }>()
</script>

<style scoped>
.page-header { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 12px 24px; margin-bottom: 24px; }
.page-header__text { flex: 1 1 420px; min-width: 0; }
.page-header__actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding-top: 2px; }
</style>
